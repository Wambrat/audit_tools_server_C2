"""
Audit Logger - Detailed logging for sensitive operations

Tracks sensitive operations with full context:
- Admin login attempts
- Task creation/modification
- Result submission
- Credential changes
- Rate limit violations
- Access to monitoring endpoints

All audit logs include: timestamp, operation, user, resource, action, status, IP, details
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class OperationType(str, Enum):
    """Types of operations to audit"""
    ADMIN_LOGIN = "admin_login"
    ADMIN_LOGOUT = "admin_logout"
    TASK_CREATION = "task_creation"
    TASK_UPDATE = "task_update"
    RESULT_SUBMISSION = "result_submission"
    AGENT_ENROLLMENT = "agent_enrollment"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    MONITORING_ACCESS = "monitoring_access"
    CREDENTIAL_CHANGE = "credential_change"


class ResourceType(str, Enum):
    """Types of resources being accessed"""
    AGENT = "agent"
    TASK = "task"
    RESULT = "result"
    ADMIN = "admin"
    SYSTEM = "system"
    DEPLOYMENT = "deployment"


class ActionType(str, Enum):
    """Actions performed on resources"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    AUTHENTICATE = "authenticate"
    AUTHORIZE = "authorize"
    MSI_BUILD = "msi_build"


class AuditLogger:
    """
    Comprehensive audit logging for security and compliance.
    
    Features:
    - Structured JSON output
    - Timestamp tracking
    - IP address capture
    - Operation context
    - Status tracking (success/failure)
    - Detailed metadata
    """
    
    def __init__(self, logger_name: str = "audit"):
        """Initialize audit logger"""
        self.logger = logging.getLogger(logger_name)
    
    def log_operation(
        self,
        operation: OperationType,
        user: str,
        resource: ResourceType,
        action: ActionType,
        status: str,  # "success" or "failure"
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Log a sensitive operation.
        
        Args:
            operation: Type of operation (admin_login, task_creation, etc.)
            user: Username or agent_id performing the action
            resource: Type of resource being accessed
            action: Action performed (create, read, update, delete)
            status: "success" or "failure"
            ip_address: Client IP address (optional)
            details: Additional metadata about the operation
            reason: Reason for failure (if status="failure")
        """
        audit_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation": operation.value,
            "user": user,
            "resource": resource.value,
            "action": action.value,
            "status": status,
        }
        
        if ip_address:
            audit_record["ip_address"] = ip_address
        
        if reason:
            audit_record["reason"] = reason
        
        if details:
            audit_record["details"] = details
        
        # Log at INFO level for successful operations, WARNING for failures
        log_level = logging.WARNING if status == "failure" else logging.INFO
        self.logger.log(log_level, json.dumps(audit_record))
    
    def log_action(
        self,
        action_type: ActionType,
        resource_type: ResourceType,
        resource_id: str,
        details: str,
        status: str,
        user: str = "system"
    ) -> None:
        """
        Generic action logging for API operations.
        
        Args:
            action_type: Type of action (MSI_BUILD, etc.)
            resource_type: Type of resource (DEPLOYMENT, etc.)
            resource_id: ID of the resource
            details: Detailed description of the action
            status: "STARTED", "SUCCESS", "FAILED", "TIMEOUT", "ERROR"
            user: User performing the action (default: "system")
        """
        audit_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action_type": action_type.value,
            "resource_type": resource_type.value,
            "resource_id": resource_id,
            "user": user,
            "status": status,
            "details": details
        }
        
        # Log level based on status
        log_level = logging.INFO if status == "SUCCESS" else logging.WARNING
        self.logger.log(log_level, json.dumps(audit_record))
    
    def log_admin_login(
        self,
        username: str,
        status: str,  # "success" or "failure"
        ip_address: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        """Log admin login attempt"""
        self.log_operation(
            operation=OperationType.ADMIN_LOGIN,
            user=username,
            resource=ResourceType.ADMIN,
            action=ActionType.AUTHENTICATE,
            status=status,
            ip_address=ip_address,
            reason=reason,
            details={
                "login_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    def log_task_creation(
        self,
        user: str,
        agent_id: str,
        task_id: str,
        command: str,
        priority: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log task creation"""
        self.log_operation(
            operation=OperationType.TASK_CREATION,
            user=user,
            resource=ResourceType.TASK,
            action=ActionType.CREATE,
            status="success",
            ip_address=ip_address,
            details={
                "task_id": task_id,
                "agent_id": agent_id,
                "command": command,
                "priority": priority,
                "creation_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    def log_result_submission(
        self,
        agent_id: str,
        task_id: str,
        result_size_bytes: int,
        status: str,  # execution status
        execution_time_ms: float,
        ip_address: Optional[str] = None
    ) -> None:
        """Log result submission"""
        self.log_operation(
            operation=OperationType.RESULT_SUBMISSION,
            user=agent_id,
            resource=ResourceType.RESULT,
            action=ActionType.CREATE,
            status="success",
            ip_address=ip_address,
            details={
                "task_id": task_id,
                "result_status": status,
                "result_size_bytes": result_size_bytes,
                "execution_time_ms": execution_time_ms,
                "submission_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    def log_agent_enrollment(
        self,
        agent_id: str,
        agent_name: str,
        hostname: str,
        ip_address: Optional[str] = None
    ) -> None:
        """Log agent enrollment"""
        self.log_operation(
            operation=OperationType.AGENT_ENROLLMENT,
            user=agent_id,
            resource=ResourceType.AGENT,
            action=ActionType.CREATE,
            status="success",
            ip_address=ip_address,
            details={
                "agent_name": agent_name,
                "hostname": hostname,
                "enrollment_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    def log_rate_limit_exceeded(
        self,
        entity_id: str,
        endpoint: str,
        limit: int,
        window_seconds: int,
        ip_address: Optional[str] = None
    ) -> None:
        """Log rate limit violation"""
        self.log_operation(
            operation=OperationType.RATE_LIMIT_EXCEEDED,
            user=entity_id,
            resource=ResourceType.SYSTEM,
            action=ActionType.AUTHORIZE,
            status="failure",
            ip_address=ip_address,
            reason="Rate limit exceeded",
            details={
                "endpoint": endpoint,
                "limit": limit,
                "window_seconds": window_seconds,
                "violation_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
    
    def log_monitoring_access(
        self,
        user: str,
        endpoint: str,
        status: str,  # "success" or "failure"
        ip_address: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        """Log access to monitoring endpoint"""
        self.log_operation(
            operation=OperationType.MONITORING_ACCESS,
            user=user,
            resource=ResourceType.SYSTEM,
            action=ActionType.READ,
            status=status,
            ip_address=ip_address,
            reason=reason,
            details={
                "endpoint": endpoint,
                "access_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


# Global audit logger instance
_audit_logger_instance = None


def get_audit_logger() -> AuditLogger:
    """Get or create audit logger singleton"""
    global _audit_logger_instance
    if _audit_logger_instance is None:
        _audit_logger_instance = AuditLogger()
    return _audit_logger_instance
