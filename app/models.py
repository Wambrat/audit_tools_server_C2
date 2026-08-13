from __future__ import annotations

import json
from pydantic import BaseModel
from typing import Optional, List, Union
from enum import Enum
from datetime import datetime


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPROMISED = "compromised"


# ===== Request/Response Models =====

class EnrollRequest(BaseModel):
    """Modèle pour l'enregistrement initial d'un agent"""
    agent_name: str
    os_version: str
    hostname: str
    username: str


class EnrollResponse(BaseModel):
    """Réponse après enregistrement"""
    agent_id: str
    api_key: str
    message: str


class BeaconRequest(BaseModel):
    """Modèle pour le heartbeat et récupération des tâches"""
    agent_id: str
    api_key: str
    status: str
    last_task_id: Optional[str] = None
    uptime_seconds: int


class TaskModel(BaseModel):
    """Modèle d'une tâche"""
    task_id: str
    command: str
    parameters: Optional[dict] = None
    priority: int = 0
    timeout_seconds: int = 300


class BeaconResponse(BaseModel):
    """Réponse avec les tâches en attente"""
    tasks: List[TaskModel]
    next_beacon_interval: int  # en secondes


class TaskCreateRequest(BaseModel):
    """Modèle pour créer une tâche via le dashboard"""
    command: str
    parameters: Optional[dict] = None
    priority: int = 0


class AuditResultRequest(BaseModel):
    """Modèle pour soumettre un résultat d'audit"""
    agent_id: str
    api_key: str
    task_id: str
    status: str  # "success" ou "failed"
    result: Union[dict, str]  # Peut être un dict ou une chaîne (PowerShell output)
    execution_time_ms: int
    error_message: Optional[str] = None


class AuditResultResponse(BaseModel):
    """Réponse après traitement du résultat"""
    message: str
    acknowledged: bool


class AuditTemplateCreateRequest(BaseModel):
    """Modèle pour créer une configuration d'audit à partir d'un ensemble de commandes PowerShell"""
    name: str
    description: str = ""
    commands: List[str]
    created_by: str = "admin"


class AuditTemplateResponse(BaseModel):
    """Réponse après création ou récupération d'une configuration d'audit"""
    template_id: str
    name: str
    description: str
    commands: List[str]
    created_by: str
    created_at: datetime
    enabled: bool = True


class AuditTemplate(BaseModel):
    """Modèle de base de données pour une configuration d'audit"""
    template_id: str
    name: str
    description: str
    commands: List[str]
    created_by: str
    created_at: datetime
    enabled: bool = True


class PowerShellCommandCreateRequest(BaseModel):
    """Modèle pour enregistrer une commande PowerShell réutilisable."""
    name: str
    description: str = ""
    script: str
    created_by: str = "admin"


class PowerShellCommandDefinition(BaseModel):
    """Version persistée d'une commande PowerShell utilisable dans les templates."""
    command_id: str
    name: str
    description: str = ""
    script: str
    created_by: str = "admin"
    created_at: datetime
    enabled: bool = True


# ===== Database Models =====

class Agent(BaseModel):
    """Modèle de base de données pour un agent"""
    agent_id: str
    api_key: str
    agent_name: str
    os_version: str
    hostname: str
    username: str
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: datetime
    last_beacon: Optional[datetime] = None


class Task(BaseModel):
    """Modèle de base de données pour une tâche"""
    task_id: str
    agent_id: str
    command: str
    parameters: Optional[dict] = None
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    timeout_seconds: int = 300
    created_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AuditResult(BaseModel):
    """Modèle de base de données pour un résultat d'audit
    
    Champs de chiffrement:
    - result_encrypted: Contenu chiffré AES-256-GCM (base64)
    - result_hash: SHA-256 du contenu plaintext (pour recherche)
    - result_preview: Résumé non-sensible (structure, taille, nb lignes)
    - result: Plaintext original (stocké en mémoire seulement, pas en BD)
    """
    result_id: str
    task_id: str
    agent_id: str
    status: str
    result_encrypted: str = ""  # Chiffré AES-256-GCM (optionnel pour tests)
    result_hash: str = ""        # SHA-256(plaintext) (optionnel pour tests)
    result_preview: str = ""     # "Output: 2500 bytes, 45 lines" (optionnel pour tests)
    result: Optional[Union[dict, str]] = None  # Plaintext (optionnel, pas stocké en BD)
    execution_time_ms: int = 0
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class BeaconHistory(BaseModel):
    """Modèle d'historique de beacon"""
    beacon_id: str
    agent_id: str
    beacon_status: str
    uptime_seconds: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    tasks_count: int = 0
    created_at: datetime


# ===== Admin Authentication Models =====

class AdminLoginRequest(BaseModel):
    """Modèle pour la connexion admin"""
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    """Réponse après connexion admin réussie"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Secondes
    message: str
