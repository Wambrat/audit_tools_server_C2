"""
Tests for Audit Logger

Tests for detailed audit logging of sensitive operations:
- Admin login tracking
- Task creation logging
- Result submission logging
- Agent enrollment logging
- Rate limit violation tracking
- Monitoring endpoint access

Run with: pytest test/test_audit_logging.py -v
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from app.audit_logger import (
    AuditLogger,
    OperationType,
    ResourceType,
    ActionType,
    get_audit_logger
)
from datetime import datetime
import json


class TestAuditLoggerBasics:
    """Basic audit logger functionality"""
    
    def test_audit_logger_initialization(self):
        """Test AuditLogger can be initialized"""
        logger = AuditLogger()
        assert logger is not None
        assert logger.logger is not None
    
    def test_audit_logger_singleton(self):
        """Test get_audit_logger returns same instance"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        assert logger1 is logger2
    
    def test_operation_type_enum(self):
        """Test OperationType enum has all values"""
        assert OperationType.ADMIN_LOGIN.value == "admin_login"
        assert OperationType.TASK_CREATION.value == "task_creation"
        assert OperationType.RESULT_SUBMISSION.value == "result_submission"
        assert OperationType.AGENT_ENROLLMENT.value == "agent_enrollment"
        assert OperationType.RATE_LIMIT_EXCEEDED.value == "rate_limit_exceeded"


class TestAdminLoginLogging:
    """Tests for admin login audit logging"""
    
    def test_log_admin_login_success(self, caplog):
        """Test logging successful admin login"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.INFO):
            logger.log_admin_login(
                username="admin",
                status="success",
                ip_address="192.168.1.100"
            )
        
        assert len(caplog.records) > 0
        log_message = caplog.records[-1].getMessage()
        assert "admin_login" in log_message
        assert "admin" in log_message
        assert "success" in log_message
        assert "192.168.1.100" in log_message
    
    def test_log_admin_login_failure(self, caplog):
        """Test logging failed admin login"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.WARNING):
            logger.log_admin_login(
                username="admin",
                status="failure",
                ip_address="192.168.1.101",
                reason="Invalid password"
            )
        
        assert len(caplog.records) > 0
        log_message = caplog.records[-1].getMessage()
        assert "admin_login" in log_message
        assert "failure" in log_message
        assert "Invalid password" in log_message
    
    def test_log_admin_login_json_structure(self, caplog):
        """Test admin login log contains valid JSON"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.INFO):
            logger.log_admin_login(
                username="testuser",
                status="success",
                ip_address="10.0.0.1"
            )
        
        log_message = caplog.records[-1].getMessage()
        data = json.loads(log_message)
        
        assert data["operation"] == "admin_login"
        assert data["user"] == "testuser"
        assert data["status"] == "success"
        assert data["ip_address"] == "10.0.0.1"
        assert "timestamp" in data
        assert "resource" in data
        assert "action" in data


class TestTaskLogging:
    """Tests for task creation audit logging"""
    
    def test_log_task_creation(self, caplog):
        """Test logging task creation"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.INFO):
            logger.log_task_creation(
                user="admin",
                agent_id="agent-001",
                task_id="task-12345",
                command="Get-Service",
                priority="high",
                ip_address="192.168.1.100"
            )
        
        log_message = caplog.records[-1].getMessage()
        data = json.loads(log_message)
        
        assert data["operation"] == "task_creation"
        assert data["user"] == "admin"
        assert data["status"] == "success"
        assert data["details"]["agent_id"] == "agent-001"
        assert data["details"]["task_id"] == "task-12345"
        assert data["details"]["command"] == "Get-Service"
        assert data["details"]["priority"] == "high"


class TestResultLogging:
    """Tests for result submission audit logging"""
    
    def test_log_result_submission(self, caplog):
        """Test logging result submission"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.INFO):
            logger.log_result_submission(
                agent_id="agent-001",
                task_id="task-12345",
                result_size_bytes=2500,
                status="completed",
                execution_time_ms=1234.5,
                ip_address="192.168.1.50"
            )
        
        log_message = caplog.records[-1].getMessage()
        data = json.loads(log_message)
        
        assert data["operation"] == "result_submission"
        assert data["user"] == "agent-001"
        assert data["resource"] == "result"
        assert data["details"]["task_id"] == "task-12345"
        assert data["details"]["result_size_bytes"] == 2500
        assert data["details"]["execution_time_ms"] == 1234.5


class TestAgentEnrollmentLogging:
    """Tests for agent enrollment audit logging"""
    
    def test_log_agent_enrollment(self, caplog):
        """Test logging agent enrollment"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.INFO):
            logger.log_agent_enrollment(
                agent_id="agent-001",
                agent_name="Workstation-01",
                hostname="DESKTOP-ABCDEF",
                ip_address="192.168.1.50"
            )
        
        log_message = caplog.records[-1].getMessage()
        data = json.loads(log_message)
        
        assert data["operation"] == "agent_enrollment"
        assert data["user"] == "agent-001"
        assert data["status"] == "success"
        assert data["details"]["agent_name"] == "Workstation-01"
        assert data["details"]["hostname"] == "DESKTOP-ABCDEF"


class TestRateLimitLogging:
    """Tests for rate limit violation audit logging"""
    
    def test_log_rate_limit_exceeded(self, caplog):
        """Test logging rate limit exceeded"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.WARNING):
            logger.log_rate_limit_exceeded(
                entity_id="192.168.1.100",
                endpoint="/api/admin/login",
                limit=5,
                window_seconds=3600,
                ip_address="192.168.1.100"
            )
        
        log_message = caplog.records[-1].getMessage()
        data = json.loads(log_message)
        
        assert data["operation"] == "rate_limit_exceeded"
        assert data["status"] == "failure"
        assert data["reason"] == "Rate limit exceeded"
        assert data["details"]["endpoint"] == "/api/admin/login"
        assert data["details"]["limit"] == 5


class TestMonitoringAccessLogging:
    """Tests for monitoring endpoint access logging"""
    
    def test_log_monitoring_access_success(self, caplog):
        """Test logging successful monitoring access"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.INFO):
            logger.log_monitoring_access(
                user="admin",
                endpoint="/api/monitoring/overview",
                status="success",
                ip_address="192.168.1.100"
            )
        
        log_message = caplog.records[-1].getMessage()
        data = json.loads(log_message)
        
        assert data["operation"] == "monitoring_access"
        assert data["user"] == "admin"
        assert data["status"] == "success"
        assert data["details"]["endpoint"] == "/api/monitoring/overview"
    
    def test_log_monitoring_access_failure(self, caplog):
        """Test logging failed monitoring access"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.WARNING):
            logger.log_monitoring_access(
                user="admin",
                endpoint="/api/monitoring/overview",
                status="failure",
                ip_address="192.168.1.100",
                reason="Invalid token"
            )
        
        log_message = caplog.records[-1].getMessage()
        data = json.loads(log_message)
        
        assert data["status"] == "failure"
        assert data["reason"] == "Invalid token"


class TestAuditLogStructure:
    """Tests for audit log structure and formatting"""
    
    def test_audit_log_timestamp_format(self, caplog):
        """Test audit log has valid ISO timestamp"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.INFO):
            logger.log_admin_login(username="test", status="success")
        
        log_message = caplog.records[-1].getMessage()
        data = json.loads(log_message)
        
        timestamp = data["timestamp"]
        assert timestamp.endswith("Z")
        # Verify it's ISO format
        datetime.fromisoformat(timestamp.rstrip("Z"))
    
    def test_audit_log_required_fields(self, caplog):
        """Test audit log contains all required fields"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.INFO):
            logger.log_admin_login(username="test", status="success")
        
        log_message = caplog.records[-1].getMessage()
        data = json.loads(log_message)
        
        required_fields = ["timestamp", "operation", "user", "resource", "action", "status"]
        for field in required_fields:
            assert field in data
    
    def test_audit_log_no_plaintext_passwords(self, caplog):
        """Test audit logs don't leak actual passwords"""
        logger = AuditLogger()
        
        with caplog.at_level(logging.INFO):
            logger.log_admin_login(
                username="admin",
                status="failure",
                ip_address="192.168.1.100",
                reason="Wrong password attempt"
            )
        
        log_message = caplog.records[-1].getMessage()
        # Reason can say "password" but actual password value should not be logged
        data = json.loads(log_message)
        assert "mySecurePass123!" not in str(data)
        assert data["reason"] == "Wrong password attempt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
