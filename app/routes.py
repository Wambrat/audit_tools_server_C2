import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Header, Depends, Request
from fastapi.responses import FileResponse
from .models import (
    EnrollRequest, EnrollResponse,
    BeaconRequest, BeaconResponse, TaskModel, TaskCreateRequest,
    AuditResultRequest, AuditResultResponse,
    AdminLoginRequest, AdminLoginResponse,
    AuditTemplateCreateRequest, AuditTemplateResponse, AuditTemplate,
    PowerShellCommandCreateRequest, PowerShellCommandDefinition,
    AgentStatus
)
from .db import get_db
from .auth import verify_agent_credentials
from .admin_auth import (
    verify_admin_credentials, create_jwt_token, verify_jwt_token,
    extract_token_from_header, TokenExpiredError, TokenInvalidError
)
from .logger import get_logger
from .rate_limiter import rate_limiter
from .audit_logger import get_audit_logger, OperationType, ResourceType, ActionType
from .monitoring import (
    get_system_overview, get_agents_dashboard, 
    get_tasks_dashboard, get_results_dashboard, get_alerts
)
import os
import shutil
import urllib.parse
from typing import Optional
import subprocess
import json as json_module
from pydantic import BaseModel

logger = get_logger(__name__)
audit_logger = get_audit_logger()
router = APIRouter(prefix="/api")


# ===== Pydantic Models for Config =====
class AgentConfigModel(BaseModel):
    serverUrl: str
    beaconInterval: int
    logFile: str
    logLevel: str = "INFO"


class ScheduledTaskConfigModel(BaseModel):
    taskName: str = "jadusAgentBeacon"
    triggerInterval: int = 30
    runWithHighestPrivileges: bool = True
    runUser: str = "SYSTEM"


class InstallationConfigModel(BaseModel):
    version: str = "1.0.0"
    installDate: str
    autoStart: bool = True


class ConfigJsonModel(BaseModel):
    agent: AgentConfigModel
    scheduled_task: ScheduledTaskConfigModel
    installation: InstallationConfigModel


class ConfigUpdateModel(BaseModel):
    serverUrl: Optional[str] = None
    beaconInterval: Optional[int] = None
    logFile: Optional[str] = None
    logLevel: Optional[str] = None
    gmsaAccount: Optional[str] = None


def verify_jwt_admin(authorization: Optional[str] = Header(None)) -> dict:
    """
    Dependency to verify JWT token for admin endpoints.
    """
    if not authorization:
        logger.warning("Admin endpoint accessed without Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = extract_token_from_header(authorization)
    if not token:
        logger.warning("Admin endpoint accessed with invalid Authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format (use: Bearer <token>)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_jwt_token(token)
        return payload
    except TokenExpiredError:
        logger.warning("Admin endpoint accessed with expired JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        logger.warning(f"Admin endpoint accessed with invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Configuration du rate limiting depuis les variables d'environnement
ENROLL_RATE_LIMIT = int(os.getenv("ENROLL_RATE_LIMIT", 5))  # 5 requÃªtes
ENROLL_WINDOW = int(os.getenv("ENROLL_WINDOW_SECONDS", 3600))  # Par heure

BEACON_RATE_LIMIT = int(os.getenv("BEACON_RATE_LIMIT", 7200))  # 7200 requÃªtes
BEACON_WINDOW = int(os.getenv("BEACON_WINDOW_SECONDS", 3600))  # Par heure

RESULTS_RATE_LIMIT = int(os.getenv("RESULTS_RATE_LIMIT", 50))  # 50 requÃªtes
RESULTS_WINDOW = int(os.getenv("RESULTS_WINDOW_SECONDS", 3600))  # Par heure


@router.post("/enroll", response_model=EnrollResponse, tags=["Agents"], 
             summary="Enroll new agent",
             responses={
                 200: {"description": "Agent enrolled successfully"},
                 409: {"description": "Agent already enrolled"},
                 429: {"description": "Rate limit exceeded"},
             })
async def enroll_agent(request: EnrollRequest):
    """
    **First connection** - Agent enrolls to receive unique ID and API key.

    This endpoint is called once when the PowerShell agent starts for the first time.
    It generates a unique `agent_id` and `api_key` that must be used for all subsequent requests.

    ### Request Body
    - `agent_name`: Friendly name for the agent
    - `os_version`: Windows OS version (e.g., "Windows Server 2019")
    - `hostname`: Computer name
    - `username`: Currently logged-in user

    ### Response
    Returns the agent credentials to store for future requests:
    - `agent_id`: Unique UUID for this agent
    - `api_key`: API key for authentication
    - `message`: Status message

    ### Rate Limit
    5 requests per hour per host (to prevent abuse)

    ### Example
    ```json
    {
      "agent_name": "DC-Audit-Agent-01",
      "os_version": "Windows Server 2022",
      "hostname": "DC-01",
      "username": "DOMAIN\\SYSTEM"
    }
    ```
    """
    db = get_db()
    
    # Utiliser hostname:username comme identifiant temporaire pour le rate limiting
    temp_agent_id = f"{request.hostname}:{request.username}"
    
    # VÃ©rifier le rate limit (sans authentification car c'est l'enroll)
    allowed, requests_made, requests_remaining = rate_limiter.is_allowed(
        agent_id=temp_agent_id,
        endpoint="enroll",
        max_requests=ENROLL_RATE_LIMIT,
        window_seconds=ENROLL_WINDOW
    )
    
    if not allowed:
        logger.warning(
            f"Enrollment rate limit exceeded for {request.hostname}\\{request.username} (max: {ENROLL_RATE_LIMIT})"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many enrollment requests. Max {ENROLL_RATE_LIMIT} per {ENROLL_WINDOW}s"
        )
    
    logger.info(
        f"Agent enrollment requested: {request.agent_name} ({request.hostname}\\{request.username})"
    )
    
    # Si l'agent s'est dÃ©jÃ  enregistrÃ© sur ce host/user, on gÃ¨re le cas actif vs inactif
    existing = db.get_agent_by_identity(request.hostname, request.username)
    if existing:
        current_status = existing.status
        if current_status == AgentStatus.ACTIVE:
            logger.warning(
                f"Enrollment rejected - agent already active: {request.hostname}\\{request.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Agent already active on this host. Please wait for the current session to disconnect before re-enrolling."
            )

        existing.agent_name = request.agent_name
        existing.os_version = request.os_version
        existing.status = AgentStatus.ACTIVE
        existing.last_beacon = datetime.now()
        logger.info(
            f"Agent reconnected and resumed session: {request.agent_name} ({existing.agent_id})"
        )
        return EnrollResponse(
            agent_id=existing.agent_id,
            api_key=existing.api_key,
            message=f"Agent {request.agent_name} resumed previous session"
        )
    
    # CrÃ©er le nouvel agent
    agent = db.create_agent(
        agent_name=request.agent_name,
        os_version=request.os_version,
        hostname=request.hostname,
        username=request.username
    )
    
    logger.info(
        f"Agent enrolled successfully: {request.agent_name} (ID: {agent.agent_id})"
    )
    
    return EnrollResponse(
        agent_id=agent.agent_id,
        api_key=agent.api_key,
        message=f"Agent {request.agent_name} enrolled successfully"
    )


@router.post("/beacon", response_model=BeaconResponse, tags=["Agents"],
             summary="Send heartbeat and get tasks",
             responses={
                 200: {"description": "Tasks returned"},
                 401: {"description": "Invalid credentials"},
                 429: {"description": "Rate limit exceeded"},
             })
async def beacon(request: BeaconRequest):
    """
    **Heartbeat** - Send agent status and receive pending tasks.

    Called regularly by agents (recommended: every 60 seconds) to:
    1. Confirm the agent is still online
    2. Get any pending tasks from the dashboard
    3. Record uptime and other metrics

    ### Request Body
    - `agent_id`: Agent's unique UUID
    - `api_key`: Agent's API key
    - `status`: Agent status (e.g., "online")
    - `uptime_seconds`: How long the agent has been running
    - `last_task_id`: Optional, ID of last completed task

    ### Response
    Returns pending tasks and recommended beacon interval:
    - `tasks`: Array of tasks to execute
    - `next_beacon_interval`: Seconds until next beacon (typically 60)

    ### Rate Limit
    100 requests per hour per agent

    ### Example
    ```json
    {
      "agent_id": "a1b2c3d4-...",
      "api_key": "f7a8b9c0-...",
      "status": "online",
      "uptime_seconds": 86400,
      "last_task_id": null
    }
    ```
    """
    db = get_db()
    
    # VÃ©rifier le rate limit avant l'authentification
    allowed, requests_made, requests_remaining = rate_limiter.is_allowed(
        agent_id=request.agent_id,
        endpoint="beacon",
        max_requests=BEACON_RATE_LIMIT,
        window_seconds=BEACON_WINDOW
    )
    
    if not allowed:
        logger.warning(
            f"Beacon rate limit exceeded for agent {request.agent_id} (max: {BEACON_RATE_LIMIT})"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many beacon requests. Max {BEACON_RATE_LIMIT} per {BEACON_WINDOW}s"
        )
    
    logger.debug(
        f"Beacon received from {request.agent_id}: status={request.status}, uptime={request.uptime_seconds}s"
    )
    
    # Authentifier l'agent
    agent = verify_agent_credentials(request.agent_id, request.api_key)
    
    # Mettre Ã  jour le timestamp du beacon
    db.update_agent_beacon(request.agent_id)
    
    # RÃ©cupÃ©rer les tÃ¢ches en attente
    pending_tasks = db.get_pending_tasks(request.agent_id)
    
    # Enregistrer le beacon dans l'historique
    db.record_beacon(
        agent_id=request.agent_id,
        beacon_status=request.status,
        uptime_seconds=request.uptime_seconds,
        tasks_count=len(pending_tasks)
    )
    
    logger.info(
        f"Tasks assigned to agent {request.agent_id}: {len(pending_tasks)} tasks, {requests_remaining} requests remaining"
    )
    
    # Convertir les tÃ¢ches en TaskModel
    tasks_response = []
    for task in pending_tasks:
        db.mark_task_assigned(task.task_id)
        tasks_response.append(
            TaskModel(
                task_id=task.task_id,
                command=task.command,
                parameters=task.parameters,
                priority=task.priority,
                timeout_seconds=task.timeout_seconds
            )
        )
    
    return BeaconResponse(
        tasks=tasks_response,
        next_beacon_interval=30  # L'agent va re-beacon dans 30 secondes
    )


@router.post("/results", response_model=AuditResultResponse, tags=["Results"],
             summary="Submit audit result",
             responses={
                 200: {"description": "Result received and encrypted"},
                 401: {"description": "Invalid credentials"},
                 429: {"description": "Rate limit exceeded"},
             })
async def submit_result(request: AuditResultRequest):
    """
    **Submit Result** - Agent submits the result of an executed audit task.

    After executing a task, the agent sends the result back to the API.
    Results are automatically encrypted with AES-256-GCM before storage.

    ### Request Body
    - `agent_id`: Agent's unique UUID
    - `api_key`: Agent's API key
    - `task_id`: The task that was executed
    - `status`: Execution status ("success" or "failed")
    - `result`: The audit output (string or JSON)
    - `execution_time_ms`: How long the task took
    - `error_message`: Error details if status is "failed"

    ### Response
    Returns acknowledgment:
    - `message`: Status message
    - `acknowledged`: Boolean confirmation

    ### Encryption
    Results are encrypted before storage:
    - `result_encrypted`: AES-256-GCM ciphertext (stored)
    - `result_hash`: SHA-256 hash for searching
    - `result_preview`: Safe preview for UI

    ### Rate Limit
    50 requests per hour per agent

    ### Example
    ```json
    {
      "agent_id": "a1b2c3d4-...",
      "api_key": "f7a8b9c0-...",
      "task_id": "task-001",
      "status": "success",
      "result": "Name    Status\\nSSH     Running\\nWinRM   Running",
      "execution_time_ms": 1234,
      "error_message": null
    }
    ```
    """
    db = get_db()
    
    # VÃ©rifier le rate limit avant l'authentification
    allowed, requests_made, requests_remaining = rate_limiter.is_allowed(
        agent_id=request.agent_id,
        endpoint="results",
        max_requests=RESULTS_RATE_LIMIT,
        window_seconds=RESULTS_WINDOW
    )
    
    if not allowed:
        logger.warning(
            f"Results rate limit exceeded for agent {request.agent_id} (max: {RESULTS_RATE_LIMIT})"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many result submissions. Max {RESULTS_RATE_LIMIT} per {RESULTS_WINDOW}s"
        )
    
    logger.debug(
        f"Result submission received from agent {request.agent_id}: task={request.task_id}, status={request.status}"
    )
    
    # Authentifier l'agent
    agent = verify_agent_credentials(request.agent_id, request.api_key)
    
    # VÃ©rifier que la tÃ¢che existe
    task = db.get_task(request.task_id)
    if not task:
        logger.warning(
            f"Result submission for non-existent task: agent={request.agent_id}, task={request.task_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {request.task_id} not found"
        )
    
    # VÃ©rifier que la tÃ¢che appartient Ã  cet agent
    if task.agent_id != request.agent_id:
        logger.warning(
            f"Unauthorized result submission: agent={request.agent_id} attempted to submit task owned by {task.agent_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Task does not belong to this agent"
        )
    
    # Enregistrer le rÃ©sultat
    audit_result = db.store_result(
        task_id=request.task_id,
        agent_id=request.agent_id,
        status=request.status,
        result=request.result,
        execution_time_ms=request.execution_time_ms,
        error_message=request.error_message
    )
    
    logger.info(
        f"Audit result recorded: agent={request.agent_id}, task={request.task_id}, status={request.status}, time={request.execution_time_ms}ms"
    )
    
    # Audit log result submission
    if isinstance(request.result, (dict, list)):
        result_serialized = json.dumps(request.result, ensure_ascii=False, default=str)
        result_size = len(result_serialized.encode('utf-8'))
    elif isinstance(request.result, str):
        result_size = len(request.result.encode('utf-8'))
    else:
        result_size = len(str(request.result).encode('utf-8')) if request.result is not None else 0

    audit_logger.log_result_submission(
        agent_id=request.agent_id,
        task_id=request.task_id,
        result_size_bytes=result_size,
        status=request.status,
        execution_time_ms=request.execution_time_ms
    )
    
    return AuditResultResponse(
        message=f"Result for task {request.task_id} acknowledged",
        acknowledged=True
    )


# ===== Endpoints de gestion (optionnel pour les tests) =====

@router.get("/agents", tags=["Agents"], summary="List all agents",
            responses={200: {"description": "List of enrolled agents"}})
async def list_agents():
    """
    **List Agents** - Get all enrolled agents and their status.
    
    Returns summary information for each agent including:
    - agent_id: Unique identifier
    - agent_name: Friendly name
    - status: Current status (active/inactive)
    - hostname: Computer name
    - last_beacon: When last heartbeat was received
    """
    db = get_db()
    agents = db.list_agents()
    return {
        "count": len(agents),
        "agents": [
            {
                "agent_id": a.agent_id,
                "agent_name": a.agent_name,
                "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
                "hostname": a.hostname,
                "last_beacon": a.last_beacon.isoformat() if a.last_beacon else None
            }
            for a in agents
        ]
    }


@router.get("/debug/agents-debug", tags=["Debug"])
async def debug_agents():
    """DEBUG - Affiche l'Ã©tat dÃ©taillÃ© des agents"""
    db = get_db()
    agents = db.list_agents()
    
    debug_data = []
    for a in agents:
        debug_data.append({
            "agent_id": a.agent_id,
            "agent_name": a.agent_name,
            "status": str(a.status),
            "status_value": a.status.value if hasattr(a.status, 'value') else str(a.status),
            "status_type": str(type(a.status)),
            "has_value_attr": hasattr(a.status, 'value'),
            "last_beacon": a.last_beacon.isoformat() if a.last_beacon else None,
        })
    
    return {
        "total": len(agents),
        "agents": debug_data
    }


@router.get("/tasks/{agent_id}")
async def list_agent_tasks(agent_id: str):
    """Lister les tÃ¢ches d'un agent"""
    db = get_db()
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    tasks = db.list_tasks(agent_id)
    return {
        "agent_id": agent_id,
        "task_count": len(tasks),
        "tasks": [
            {
                "task_id": t.task_id,
                "command": t.command,
                "status": t.status,
                "created_at": t.created_at,
                "priority": t.priority
            }
            for t in tasks
        ]
    }


@router.post("/tasks/{agent_id}")
async def create_task(agent_id: str, task_request: TaskCreateRequest):
    """CrÃ©er une nouvelle tÃ¢che pour un agent (endpoint de gestion)
    
    Body JSON:
    {
      "command": "Get-AuditPolicy",
      "parameters": {...},
      "priority": 0
    }
    """
    db = get_db()
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    task = db.create_task(
        agent_id=agent_id,
        command=task_request.command,
        parameters=task_request.parameters,
        priority=task_request.priority
    )
    
    logger.info(
        f"Management task created: agent={agent_id}, task={task.task_id}, command={task_request.command}"
    )
    
    # Audit log task creation
    audit_logger.log_task_creation(
        user="admin",  # Management endpoint
        agent_id=agent_id,
        task_id=task.task_id,
        command=task_request.command,
        priority=str(task_request.priority)
    )
    
    return {
        "task_id": task.task_id,
        "status": task.status,
        "message": f"Task created for agent {agent_id}"
    }


@router.get("/powershell-commands", tags=["PowerShell Commands"], summary="List registered PowerShell commands")
async def list_powershell_commands(admin_user = Depends(verify_jwt_admin)):
    """Retourne la liste des commandes PowerShell utilisables dans les templates."""
    db = get_db()
    commands = db.list_powershell_commands()
    return {
        "count": len(commands),
        "commands": [
            {
                "command_id": cmd.command_id,
                "name": cmd.name,
                "description": cmd.description,
                "script": cmd.script,
                "created_by": cmd.created_by,
                "created_at": cmd.created_at.isoformat() if hasattr(cmd.created_at, 'isoformat') else cmd.created_at,
                "enabled": cmd.enabled,
            }
            for cmd in commands
        ]
    }


@router.post("/powershell-commands", tags=["PowerShell Commands"], summary="Create a reusable PowerShell command")
async def create_powershell_command(command: PowerShellCommandCreateRequest, admin_user = Depends(verify_jwt_admin)):
    """Enregistre une commande PowerShell ou une fonction custom pour les templates."""
    db = get_db()
    try:
        created = db.create_powershell_command(
            name=command.name,
            description=command.description,
            script=command.script,
            created_by=command.created_by or admin_user.get("username", "admin"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info(f"PowerShell command created by {admin_user.get('username', 'admin')}: {created.name}")
    return {
        "command_id": created.command_id,
        "name": created.name,
        "description": created.description,
        "script": created.script,
        "created_by": created.created_by,
        "created_at": created.created_at.isoformat(),
        "enabled": created.enabled,
    }


@router.put("/powershell-commands/{command_id}", tags=["PowerShell Commands"], summary="Update a saved PowerShell command")
async def update_powershell_command(command_id: str, command: PowerShellCommandCreateRequest, admin_user = Depends(verify_jwt_admin)):
    """Met Ã  jour une commande PowerShell enregistrÃ©e."""
    db = get_db()
    try:
        updated = db.update_powershell_command(
            command_id,
            name=command.name,
            description=command.description,
            script=command.script,
            created_by=command.created_by or admin_user.get("username", "admin"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info(f"PowerShell command updated by {admin_user.get('username', 'admin')}: {updated.name}")
    return {
        "command_id": updated.command_id,
        "name": updated.name,
        "description": updated.description,
        "script": updated.script,
        "created_by": updated.created_by,
        "created_at": updated.created_at.isoformat(),
        "enabled": updated.enabled,
    }


@router.delete("/powershell-commands/{command_id}", tags=["PowerShell Commands"], summary="Delete a saved PowerShell command")
async def delete_powershell_command(command_id: str, admin_user = Depends(verify_jwt_admin)):
    """Supprime une commande PowerShell enregistrÃ©e."""
    db = get_db()
    deleted = db.delete_powershell_command(command_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Command not found")

    logger.info(f"PowerShell command deleted by {admin_user.get('username', 'admin')}: {command_id}")
    return {"message": "Command deleted successfully", "command_id": command_id}


@router.post("/audit-templates", response_model=AuditTemplateResponse, tags=["Audit Templates"],
             summary="Upload and store an audit configuration",
             responses={
                 200: {"description": "Audit template stored successfully"},
                 401: {"description": "Unauthorized - JWT required"},
                 400: {"description": "Invalid command list"},
             })
async def create_audit_template(template: AuditTemplateCreateRequest, admin_user = Depends(verify_jwt_admin)):
    """CrÃ©er une configuration d'audit administrateur contenant une liste de commandes PowerShell."""
    db = get_db()
    try:
        stored_template = db.create_audit_template(
            name=template.name,
            description=template.description,
            commands=template.commands,
            created_by=template.created_by or admin_user.get("username", "admin"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info(
        f"Audit template created by {admin_user.get('username', 'admin')}: {stored_template.template_id}"
    )
    return AuditTemplateResponse(**stored_template.model_dump())


@router.get("/audit-templates", tags=["Audit Templates"], summary="List stored audit templates")
async def list_audit_templates(admin_user = Depends(verify_jwt_admin)):
    """RÃ©cupÃ¨re toutes les configurations d'audit stockÃ©es en base."""
    db = get_db()
    templates = db.list_audit_templates()
    return {
        "count": len(templates),
        "templates": [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "commands": t.commands,
                "created_by": t.created_by,
                "created_at": t.created_at.isoformat() if hasattr(t.created_at, 'isoformat') else t.created_at,
                "enabled": t.enabled,
            }
            for t in templates
        ]
    }


@router.put("/audit-templates/{template_id}", response_model=AuditTemplateResponse, tags=["Audit Templates"],
            summary="Update an existing audit template")
async def update_audit_template(template_id: str, template: AuditTemplateCreateRequest, admin_user = Depends(verify_jwt_admin)):
    """Met Ã  jour un template d'audit existant."""
    db = get_db()
    try:
        updated_template = db.update_audit_template(
            template_id=template_id,
            name=template.name,
            description=template.description,
            commands=template.commands,
            created_by=template.created_by or admin_user.get("username", "admin"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info(f"Audit template updated by {admin_user.get('username', 'admin')}: {template_id}")
    return AuditTemplateResponse(**updated_template.model_dump())


@router.post("/audit-templates/{template_id}/duplicate", response_model=AuditTemplateResponse, tags=["Audit Templates"],
             summary="Duplicate an audit template")
async def duplicate_audit_template(template_id: str, admin_user = Depends(verify_jwt_admin)):
    """Duplique un template d'audit existant."""
    db = get_db()
    try:
        duplicated_template = db.duplicate_audit_template(template_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info(f"Audit template duplicated by {admin_user.get('username', 'admin')}: {template_id}")
    return AuditTemplateResponse(**duplicated_template.model_dump())


@router.delete("/audit-templates/{template_id}", tags=["Audit Templates"], summary="Delete an audit template")
async def delete_audit_template(template_id: str, admin_user = Depends(verify_jwt_admin)):
    """Supprime un template d'audit."""
    db = get_db()
    deleted = db.delete_audit_template(template_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    logger.info(f"Audit template deleted by {admin_user.get('username', 'admin')}: {template_id}")
    return {"message": "Template deleted successfully", "template_id": template_id}


@router.get("/audit-templates/{template_id}/export", tags=["Audit Templates"], summary="Export a template as JSON")
async def export_audit_template(template_id: str, admin_user = Depends(verify_jwt_admin)):
    """RÃ©cupÃ¨re le contenu d'un template au format JSON prÃªt Ã  rÃ©importer."""
    db = get_db()
    try:
        payload = db.export_audit_template(template_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return payload


@router.get("/audit-templates/history", tags=["Audit Templates"], summary="List template application history")
async def get_audit_template_history(admin_user = Depends(verify_jwt_admin)):
    """RÃ©cupÃ¨re l'historique des applications de templates."""
    db = get_db()
    return {"history": db.get_template_history()}


@router.post("/audit-templates/{template_id}/apply-all", tags=["Audit Templates"],
             summary="Apply one template to every registered agent")
async def apply_audit_template_to_all_agents(template_id: str, admin_user = Depends(verify_jwt_admin)):
    """Applique un template Ã  tous les agents enregistrÃ©s."""
    db = get_db()
    try:
        result = db.apply_template_to_all_agents(template_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info(f"Audit template {template_id} applied to all agents by {admin_user.get('username', 'admin')}")
    return result


@router.post("/audit-templates/{template_id}/apply/{agent_id}", tags=["Audit Templates"],
             summary="Turn an audit template into one or more tasks for an agent")
async def apply_audit_template_to_agent(template_id: str, agent_id: str, admin_user = Depends(verify_jwt_admin)):
    """Transforme une configuration d'audit en tÃ¢ches PowerShell pour un agent."""
    db = get_db()
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    try:
        tasks = db.build_tasks_from_template(template_id, agent_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.record_template_application(template_id, agent_id, len(tasks))

    logger.info(
        f"Audit template {template_id} applied to agent {agent_id} by {admin_user.get('username', 'admin')}"
    )
    return {
        "agent_id": agent_id,
        "template_id": template_id,
        "task_count": len(tasks),
        "tasks": [
            {
                "task_id": task.task_id,
                "command": task.command,
                "status": task.status,
                "parameters": task.parameters,
            }
            for task in tasks
        ],
        "message": "Audit template converted into tasks successfully"
    }


@router.get("/results/{agent_id}")
async def get_agent_results(agent_id: str):
    """RÃ©cupÃ©rer tous les rÃ©sultats d'un agent"""
    db = get_db()
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    results = db.get_results_by_agent(agent_id)
    return {
        "agent_id": agent_id,
        "result_count": len(results),
        "results": [
            {
                "result_id": r.result_id,
                "task_id": r.task_id,
                "status": r.status,
                "result": r.result,
                "error_message": r.error_message,
                "execution_time_ms": r.execution_time_ms,
                "created_at": r.created_at
            }
            for r in results
        ]
    }


@router.get("/results/detail/{result_id}")
async def get_result_detail(result_id: str):
    """RÃ©cupÃ©rer les dÃ©tails complets d'un rÃ©sultat spÃ©cifique"""
    db = get_db()
    
    try:
        # Pour la base de donnÃ©es en mÃ©moire
        if hasattr(db, 'results') and isinstance(db.results, dict):
            result = db.results.get(result_id)
            if result:
                return {
                    "result_id": result.result_id,
                    "task_id": result.task_id,
                    "agent_id": result.agent_id,
                    "status": result.status,
                    "result": result.result,
                    "error_message": result.error_message,
                    "execution_time_ms": result.execution_time_ms,
                    "created_at": result.created_at
                }
    except Exception as e:
        logger.error(f"Error retrieving result {result_id}: {e}")
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Result not found"
    )


# ===== Endpoints de monitoring du rate limiting =====

@router.get("/rate-limit/stats/{agent_id}/{endpoint}")
async def get_rate_limit_stats(agent_id: str, endpoint: str):
    """RÃ©cupÃ©rer les stats de rate limit pour un agent et endpoint"""
    stats = rate_limiter.get_stats(agent_id, endpoint)
    return stats


# ===== Endpoints d'historique =====

@router.get("/beacon-history/{agent_id}")
async def get_beacon_history(agent_id: str, limit: int = 100):
    """
    RÃ©cupÃ©rer l'historique des beacons d'un agent.
    
    - **agent_id**: ID de l'agent
    - **limit**: Nombre maximum de beacons Ã  retourner (dÃ©faut: 100)
    """
    db = get_db()
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    if limit < 1 or limit > 1000:
        limit = 100
    
    beacons = db.get_beacon_history(agent_id, limit=limit)
    
    logger.info(
        f"Beacon history retrieved for agent {agent_id}: {len(beacons)} beacons"
    )
    
    return {
        "agent_id": agent_id,
        "beacon_count": len(beacons),
        "beacons": [
            {
                "beacon_id": b.beacon_id,
                "beacon_status": b.beacon_status,
                "uptime_seconds": b.uptime_seconds,
                "tasks_count": b.tasks_count,
                "ip_address": b.ip_address,
                "created_at": b.created_at.isoformat()
            }
            for b in beacons
        ]
    }


@router.get("/beacon-stats/{agent_id}")
async def get_beacon_stats(agent_id: str):
    """
    RÃ©cupÃ©rer les statistiques de beacon pour un agent.
    
    - **agent_id**: ID de l'agent
    """
    db = get_db()
    agent = db.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    stats = db.get_beacon_stats(agent_id)
    
    logger.info(
        f"Beacon stats retrieved for agent {agent_id}: {stats['total_beacons']} total beacons"
    )
    
    return stats


@router.delete("/agents/{agent_id}", tags=["Agents"], summary="Delete an agent",
               responses={
                   200: {"description": "Agent deleted successfully"},
                   401: {"description": "Unauthorized - invalid or missing token"},
                   404: {"description": "Agent not found"},
               })
async def delete_agent(agent_id: str, admin_user = Depends(verify_jwt_admin)):
    """
    **Delete Agent** - Remove an agent and all its associated data.
    
    **Protected endpoint** - Requires valid JWT token in Authorization header.
    
    Deletes:
    - The agent record
    - All associated tasks
    - All associated results
    - All beacon history
    
    ### Request
    ```
    DELETE /api/agents/{agent_id}
    Authorization: Bearer <jwt_token>
    ```
    
    ### Response (200 OK)
    ```json
    {
      "success": true,
      "agent_id": "uuid",
      "message": "Agent deleted successfully"
    }
    ```
    
    ### Error Responses
    - **401 Unauthorized**: Missing or invalid JWT token
    - **404 Not Found**: Agent with specified ID doesn't exist
    """
    db = get_db()
    
    # Check if agent exists
    agent = db.get_agent(agent_id)
    if not agent:
        logger.warning(f"Delete agent attempt for non-existent agent: {agent_id} (user: {admin_user.get('username')})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    
    # Delete the agent
    success = db.delete_agent(agent_id)
    
    if success:
        logger.info(f"Agent {agent_id} ({agent.agent_name}) deleted by {admin_user.get('username')}")
        return {
            "success": True,
            "agent_id": agent_id,
            "message": f"Agent {agent.agent_name} deleted successfully"
        }
    else:
        logger.error(f"Failed to delete agent {agent_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent"
        )


@router.post("/admin/login", response_model=AdminLoginResponse, tags=["Admin"],
            summary="Admin login (JWT)",
            responses={
                200: {"description": "Login successful, JWT token returned"},
                401: {"description": "Invalid credentials"},
                429: {"description": "Too many login attempts - rate limited"},
            })
async def admin_login(request: AdminLoginRequest, client_ip: str = Header(None, alias="x-forwarded-for")):
    """
    **Admin Login** - Authenticate admin and receive JWT token.
    
    Use the returned JWT token in the `Authorization: Bearer <token>` header
    for all subsequent admin/monitoring requests.
    
    ### Rate Limiting
    - **5 login attempts per hour per IP address**
    - Returns HTTP 429 if exceeded
    - Includes backoff header: X-RateLimit-Reset
    
    ### Credentials
    - Default username: `admin`
    - Default password: `changeme`
    - Configure with `ADMIN_USERNAME` and `ADMIN_PASSWORD` env vars
    
    ### Token Expiration
    - Default: 24 hours
    - Configure with `JWT_EXPIRATION_HOURS` env var
    
    ### Request Body
    ```json
    {
      "username": "admin",
      "password": "changeme"
    }
    ```
    
    ### Response
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "token_type": "bearer",
      "expires_in": 86400,
      "message": "Login successful"
    }
    ```
    
    ### Usage Example (PowerShell)
    ```powershell
    # 1. Get token
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/admin/login" `
      -Method Post `
      -Headers @{"Content-Type" = "application/json"} `
      -Body (@{username = "admin"; password = "changeme"} | ConvertTo-Json)
    
    # 2. Use token for monitoring requests
    $token = $loginResponse.access_token
    $headers = @{
      "Authorization" = "Bearer $token"
      "Content-Type" = "application/json"
    }
    
    $stats = Invoke-RestMethod -Uri "http://localhost:8000/api/monitoring/overview" `
      -Headers $headers
    ```
    """
    # Extract IP from header or use localhost
    ip_address = client_ip.split(",")[0].strip() if client_ip else "localhost"
    
    # Rate limiting: 5 login attempts per hour per IP (brute force protection)
    admin_login_limit = int(os.getenv("ADMIN_LOGIN_LIMIT", 5))
    admin_login_window = int(os.getenv("ADMIN_LOGIN_WINDOW_SECONDS", 3600))
    
    allowed, requests_made, requests_remaining = rate_limiter.is_allowed(
        agent_id=ip_address,
        endpoint="/admin/login",
        max_requests=admin_login_limit,
        window_seconds=admin_login_window
    )
    
    if not allowed:
        logger.warning(
            f"Admin login rate limit exceeded for IP {ip_address} "
            f"({requests_made} requests in {admin_login_window}s)"
        )
        # Audit log rate limit exceeded
        audit_logger.log_rate_limit_exceeded(
            entity_id=ip_address,
            endpoint="/admin/login",
            limit=admin_login_limit,
            window_seconds=admin_login_window,
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"X-RateLimit-Reset": str(admin_login_window)}
        )
    
    # Verify credentials
    if not verify_admin_credentials(request.username, request.password):
        logger.warning(f"Failed admin login attempt from IP {ip_address} (user: {request.username})")
        # Audit log failed login
        audit_logger.log_admin_login(
            username=request.username,
            status="failure",
            ip_address=ip_address,
            reason="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Generate JWT token
    token = create_jwt_token(request.username)
    
    # Calculate expiration in seconds
    jwt_expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    expires_in = jwt_expiration_hours * 3600
    
    logger.info(f"Admin login successful for user '{request.username}' from IP {ip_address}")
    
    # Audit log successful login
    audit_logger.log_admin_login(
        username=request.username,
        status="success",
        ip_address=ip_address
    )
    
    return AdminLoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        message=f"Login successful. Token valid for {jwt_expiration_hours} hours."
    )


# ===== Endpoints de monitoring =====

@router.get("/monitoring/overview", tags=["Monitoring"], summary="System overview",
           responses={200: {"description": "System statistics"}})
async def monitoring_overview():
    """
    **System Overview** - Get high-level system statistics.
    
    **Required**: JWT token in `Authorization: Bearer <token>` header
    
    Returns:
    - Total agents (active, inactive)
    - Total tasks (pending, assigned, completed, failed)
    - Total results with success rate
    - Average execution time
    """
    overview = get_system_overview()
    
    logger.info(
        f"System overview retrieved: {overview['agents']['total']} agents, {overview['tasks']['total']} tasks"
    )
    
    return overview


@router.get("/monitoring/agents", tags=["Monitoring"], summary="Agents dashboard",
           responses={200: {"description": "Per-agent statistics"}})
async def monitoring_agents():
    """
    **Agents Dashboard** - Get detailed statistics for each agent.
    
    Pour chaque agent:
    - Informations de base (hostname, OS, etc.)
    - Statut de disponibilitÃ©
    - Stats de beacon
    - TÃ¢ches assignÃ©es
    - Taux de succÃ¨s des rÃ©sultats
    """
    dashboard = get_agents_dashboard()
    
    logger.info(
        f"Agents dashboard retrieved: {dashboard['total_agents']} agents"
    )
    
    return dashboard


@router.get("/monitoring/tasks", tags=["Monitoring"], summary="Tasks dashboard",
           responses={200: {"description": "Per-task statistics"}})
async def monitoring_tasks():
    """
    **Tasks Dashboard** - Get task statistics and details.
    
    **Required**: JWT token in `Authorization: Bearer <token>` header
    
    RÃ©cupÃ©rer le dashboard dÃ©taillÃ© des tÃ¢ches.
    
    Inclut:
    - TÃ¢ches par statut (pending, assigned, completed, failed)
    - TÃ¢ches en retard (timeout dÃ©passÃ©)
    - Temps d'exÃ©cution moyen
    - TÃ¢ches groupÃ©es par agent
    """
    dashboard = get_tasks_dashboard()
    
    logger.info(
        f"Tasks dashboard retrieved: {dashboard['total_tasks']} tasks ({dashboard['overdue_tasks_count']} overdue)"
    )
    
    return dashboard


@router.get("/monitoring/results", tags=["Monitoring"], summary="Results dashboard",
           responses={200: {"description": "Results statistics"}})
async def monitoring_results():
    """
    **Results Dashboard** - Get audit results statistics and details.
    
    **Required**: JWT token in `Authorization: Bearer <token>` header
    
    RÃ©cupÃ©rer le dashboard dÃ©taillÃ© des rÃ©sultats.
    
    Inclut:
    - Taux de succÃ¨s/Ã©chec
    - Temps d'exÃ©cution moyen
    - RÃ©sultats en erreur (dernier 10)
    - RÃ©sultats groupÃ©s par agent
    """
    dashboard = get_results_dashboard()
    
    logger.info(
        f"Results dashboard retrieved: {dashboard['total_results']} results (success rate: {dashboard['success']['rate_percent']}%)"
    )
    
    return dashboard


@router.get("/monitoring/alerts", tags=["Monitoring"], summary="System alerts",
           responses={200: {"description": "Active alerts"}})
async def monitoring_alerts():
    """
    **System Alerts** - Get active system alerts and warnings.
    
    **Required**: JWT token in `Authorization: Bearer <token>` header
    
    RÃ©cupÃ©rer les alertes du systÃ¨me.
    
    Types d'alertes:
    - Agents inactifs (2+ heures sans beacon)
    - Agents lents (30+ minutes sans beacon)
    - Agents jamais connectÃ©s
    - TÃ¢ches en timeout
    
    Niveau d'alerte global: ok, warning, critical
    """
    alerts = get_alerts()
    
    logger.info(
        f"Alerts retrieved: level={alerts['overall_level']}, {alerts['critical_alerts']} critical, {alerts['warning_alerts']} warnings"
    )
    
    return alerts


@router.get("/monitoring/dashboard", tags=["Monitoring"], summary="Complete dashboard",
           responses={200: {"description": "All dashboard data combined"},
                      401: {"description": "Unauthorized - JWT token required"}})
async def monitoring_dashboard(admin_user = Depends(verify_jwt_admin)):
    """
    **Complete Dashboard** - Get all monitoring data combined (overview, agents, tasks, results, alerts).
    
    **Required**: JWT token in `Authorization: Bearer <token>` header
    
    **ATTENTION**: Cet endpoint peut Ãªtre lourd. PrÃ©fÃ©rez les endpoints spÃ©cifiques.
    """
    dashboard = {
        "overview": get_system_overview(),
        "agents": get_agents_dashboard(),
        "tasks": get_tasks_dashboard(),
        "results": get_results_dashboard(),
        "alerts": get_alerts()
    }
    
    logger.info("Complete dashboard retrieved")
    
    return dashboard


# ===== Endpoints de gestion/administration =====

@router.post("/admin/reset")
async def admin_reset():
    """
    RÃ©initialiser la base de donnÃ©es (DÃ‰VELOPPEMENT UNIQUEMENT).
    Supprime tous les agents, tÃ¢ches et rÃ©sultats.
    """
    db = get_db()
    
    # RÃ©initialiser tous les stockages
    if hasattr(db, 'agents'):
        db.agents.clear()
    if hasattr(db, 'tasks'):
        db.tasks.clear()
    if hasattr(db, 'results'):
        db.results.clear()
    if hasattr(db, 'beacon_history'):
        db.beacon_history.clear()
    
    logger.warning("DATABASE RESET: All data cleared")
    
    return {
        "status": "reset",
        "message": "Database has been reset. All agents, tasks, and results have been cleared."
    }



# ===== Endpoints de Configuration MSI =====

@router.get("/admin/config", tags=["Admin", "Configuration"])
async def get_msi_config(admin_user = Depends(verify_jwt_admin)):
    """
    RÃ©cupÃ©rer la configuration actuelle pour la compilation du MSI.
    
    Endpoint sÃ©curisÃ© - NÃ©cessite un JWT token valide
    """
    
    # Charger config.json
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "installer", "config.json")
    
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration file not found"
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json_module.load(f)
        
        logger.info(f"Configuration loaded by {admin_user.get('username', 'unknown')}")
        return {
            "status": "success",
            "config": config
        }
    except Exception as e:
        logger.error(f"Failed to load config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load configuration: {str(e)}"
        )


@router.post("/admin/config", tags=["Admin", "Configuration"])
async def update_msi_config(
    config_update: ConfigUpdateModel,
    admin_user = Depends(verify_jwt_admin)
):
    """
    Mettre Ã  jour la configuration pour la compilation du MSI.
    
    Seuls les champs fournis sont mis Ã  jour.
    
    Endpoint sÃ©curisÃ© - NÃ©cessite un JWT token valide
    """
    
    # Charger config.json
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "installer", "config.json")
    
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration file not found"
        )
    
    try:
        # Charger la config existante
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json_module.load(f)
        
        # Mettre Ã  jour uniquement les champs fournis
        update_data = config_update.dict(exclude_unset=True)

        # URL serveur complète : on valide juste le schéma http/https + un host.
        if 'serverUrl' in update_data:
            new_url = (update_data.pop('serverUrl') or '').strip()
            if new_url:
                parsed = urllib.parse.urlparse(new_url)
                if parsed.scheme not in ('http', 'https') or not parsed.netloc:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="serverUrl invalide. Format attendu : http(s)://hote[:port][/chemin]"
                    )
                config.setdefault('agent', {})['serverUrl'] = new_url

        # Compte gMSA (sous scheduled_task, pas agent)
        if 'gmsaAccount' in update_data:
            config.setdefault('scheduled_task', {})['gmsaAccount'] = (update_data.pop('gmsaAccount') or '').strip()

        # Autres champs agent (beaconInterval, logFile, logLevel)
        for key, value in update_data.items():
            if key in ('beaconInterval', 'logFile', 'logLevel'):
                config.setdefault('agent', {})[key] = value

        logger.info(f"Config updated by {admin_user.get('username', 'unknown')}")

        if update_data:
            logger.info(f"Updating config with: {update_data} by {admin_user.get('username', 'unknown')}")
            
            # Mettre Ã  jour les paramÃ¨tres agent
            for key, value in update_data.items():
                if key in config.get("agent", {}):
                    config["agent"][key] = value
        
        # Sauvegarder la config mise Ã  jour
        with open(config_path, 'w', encoding='utf-8') as f:
            json_module.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info("Configuration updated successfully")
        
        # Audit log
        audit_logger.log_action(
            action_type=ActionType.UPDATE,
            resource_type=ResourceType.DEPLOYMENT,
            resource_id="jadusAgent",
            details=f"Configuration updated: {update_data}",
            status="SUCCESS"
        )
        
        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "config": config
        }
    
    except HTTPException:
        # Laisser passer les erreurs de validation (ex. 400 serverUrl invalide)
        raise
    except Exception as e:
        logger.error(f"Failed to update config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


# ===== Endpoints de gÃ©nÃ©ration du MSI =====

def resolve_powershell_executable() -> str:
    """Retourne l'exÃ©cutable PowerShell disponible sur la machine hÃ´te ou dans le conteneur."""
    env_path = os.environ.get("POWERSHELL_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    candidates = [
        env_path,
        shutil.which("pwsh"),
        shutil.which("powershell"),
        shutil.which("powershell.exe"),
        "/usr/bin/pwsh",
        "/opt/microsoft/powershell/7/pwsh",
    ]

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    raise FileNotFoundError(
        "Aucun binaire PowerShell n'a Ã©tÃ© trouvÃ©. Installez pwsh dans le backend ou configurez POWERSHELL_PATH."
    )


@router.post("/admin/build-msi", tags=["Admin", "Deployment"])
async def build_msi_package(authorization: Optional[str] = Header(None)):
    """
    Compiler le package MSI avec la configuration actuelle.
    
    Cet endpoint :
    1. VÃ©rifie les permissions admin
    2. ExÃ©cute le script build-msi.ps1
    3. Retourne le statut de compilation et le chemin du MSI
    
    Endpoint sÃ©curisÃ© - NÃ©cessite un JWT token valide
    """
    
    # VÃ©rifier l'authentification
    if not authorization:
        logger.warning("MSI build endpoint accessed without Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = extract_token_from_header(authorization)
    if not token:
        logger.warning("MSI build endpoint accessed with invalid Authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        verify_jwt_token(token)
    except (TokenExpiredError, TokenInvalidError) as e:
        logger.warning(f"MSI build endpoint accessed with invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Audit log
    audit_logger.log_action(
        action_type=ActionType.MSI_BUILD,
        resource_type=ResourceType.DEPLOYMENT,
        resource_id="jadusAgent",
        details="MSI compilation requested via API",
        status="STARTED"
    )
    
    logger.info("Starting MSI build process...")
    
    # Chemins
    installer_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "installer")
    build_script = os.path.join(installer_dir, "build-msi.ps1")
    config_file = os.path.join(installer_dir, "config.json")
    
    # VÃ©rifier que les fichiers existent
    if not os.path.exists(build_script):
        logger.error(f"Build script not found: {build_script}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Build script not found"
        )
    
    if not os.path.exists(config_file):
        logger.error(f"Config file not found: {config_file}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration file not found"
        )
    
    try:
        # ExÃ©cuter le script PowerShell
        logger.info(f"Executing build script: {build_script}")
        
        # Commande PowerShell pour exÃ©cuter build-msi.ps1
        # NOTE: Set-ExecutionPolicy n'existe que sous Windows ; sous Linux (pwsh) on l'ignore.
        ps_command = f"""
        if (-not (Test-Path variable:IsWindows) -or $IsWindows) {{ Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force }}
        & '{build_script}'
        """

        # DÃ©tecter l'interprÃ©teur PowerShell disponible de faÃ§on fiable
        # (Docker/Linux, Windows, ou variable d'environnement configurÃ©e).
        powershell_exe = resolve_powershell_executable()
        logger.info(f"Using PowerShell interpreter: {powershell_exe}")

        # ExÃ©cuter via subprocess
        result = subprocess.run(
            [powershell_exe, "-NoProfile", "-Command", ps_command],
            cwd=installer_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        logger.info(f"Build process completed with exit code: {result.returncode}")
        
        # VÃ©rifier le statut
        if result.returncode == 0:
            # Chercher le fichier MSI gÃ©nÃ©rÃ©
            msi_path = os.path.join(installer_dir, "jadusAgent.msi")
            
            if os.path.exists(msi_path):
                msi_size = os.path.getsize(msi_path) / (1024 * 1024)  # MB
                
                logger.info(f"âœ… MSI successfully built: {msi_path} ({msi_size:.2f} MB)")
                
                audit_logger.log_action(
                    action_type=ActionType.MSI_BUILD,
                    resource_type=ResourceType.DEPLOYMENT,
                    resource_id="jadusAgent",
                    details=f"MSI compiled successfully - Size: {msi_size:.2f} MB",
                    status="SUCCESS"
                )
                
                return {
                    "status": "success",
                    "message": "MSI package compiled successfully",
                    "msi_path": msi_path,
                    "msi_size_mb": round(msi_size, 2),
                    "timestamp": datetime.utcnow().isoformat(),
                    "stdout": result.stdout[-500:] if result.stdout else "",  # Last 500 chars
                }
            else:
                logger.error("Build succeeded but MSI file not found")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Build succeeded but MSI file not found"
                )
        else:
            # build-msi.ps1 Ã©crit ses logs (et l'erreur wixl) sur stdout via Write-Host,
            # pas sur stderr : on combine les deux pour ne rien perdre.
            combined_output = "\n".join(
                part for part in (result.stdout, result.stderr) if part
            ).strip()

            logger.error(f"Build failed with exit code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")

            audit_logger.log_action(
                action_type=ActionType.MSI_BUILD,
                resource_type=ResourceType.DEPLOYMENT,
                resource_id="jadusAgent",
                details=f"Build failed: {combined_output[:200]}",
                status="FAILED"
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "failed",
                    "message": "MSI build failed",
                    "error": combined_output[-1500:] if combined_output else "Unknown error",
                    "exit_code": result.returncode
                }
            )
    
    except subprocess.TimeoutExpired:
        logger.error("Build process timeout (exceeded 300 seconds)")
        
        audit_logger.log_action(
            action_type=ActionType.MSI_BUILD,
            resource_type=ResourceType.DEPLOYMENT,
            resource_id="jadusAgent",
            details="Build timeout after 300 seconds",
            status="TIMEOUT"
        )
        
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Build process timeout (exceeded 5 minutes)"
        )
    
    except Exception as e:
        logger.error(f"Build process error: {str(e)}")
        
        audit_logger.log_action(
            action_type=ActionType.MSI_BUILD,
            resource_type=ResourceType.DEPLOYMENT,
            resource_id="jadusAgent",
            details=f"Build error: {str(e)}",
            status="ERROR"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Build process error: {str(e)}"
        )



@router.get("/admin/build-msi/download", tags=["Admin", "Deployment"])
async def download_msi_package(authorization: Optional[str] = Header(None)):
    """TÃ©lÃ©charge le dernier MSI produit sâ€™il existe."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = extract_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        verify_jwt_token(token)
    except (TokenExpiredError, TokenInvalidError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    installer_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "installer")
    msi_path = os.path.join(installer_dir, "jadusAgent.msi")

    if not os.path.exists(msi_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No MSI artifact available yet. Build it first."
        )

    return FileResponse(
        path=msi_path,
        media_type="application/octet-stream",
        filename="jadusAgent.msi"
    )

