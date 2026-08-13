"""
Tests unitaires pour app/models.py
Teste la validation des modèles Pydantic
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models import (
    EnrollRequest, BeaconRequest, TaskCreateRequest,
    AuditResultRequest, Agent, Task, AuditResult,
    AgentStatus, TaskStatus,
    AuditTemplateCreateRequest, AuditTemplateResponse, AuditTemplate,
    PowerShellCommandCreateRequest, PowerShellCommandDefinition
)
from app.database import Database


class TestEnrollRequest:
    """Tests pour le modèle EnrollRequest"""
    
    def test_valid_enroll_request(self):
        """Test: EnrollRequest valide"""
        data = {
            "agent_name": "test-agent",
            "os_version": "Windows 10",
            "hostname": "DESKTOP",
            "username": "admin"
        }
        req = EnrollRequest(**data)
        
        assert req.agent_name == "test-agent"
        assert req.os_version == "Windows 10"
    
    def test_missing_required_field(self):
        """Test: Rejet si champ obligatoire manquant"""
        data = {
            "agent_name": "test-agent",
            "os_version": "Windows 10",
            # hostname manquant
            "username": "admin"
        }
        
        with pytest.raises(ValidationError):
            EnrollRequest(**data)
    
    def test_extra_fields_ignored(self):
        """Test: Les champs extra sont ignorés"""
        data = {
            "agent_name": "test-agent",
            "os_version": "Windows 10",
            "hostname": "DESKTOP",
            "username": "admin",
            "extra_field": "should_be_ignored"
        }
        req = EnrollRequest(**data)
        
        assert not hasattr(req, "extra_field")


class TestBeaconRequest:
    """Tests pour le modèle BeaconRequest"""
    
    def test_valid_beacon_request(self):
        """Test: BeaconRequest valide"""
        data = {
            "agent_id": "abc123",
            "api_key": "def456",
            "status": "online",
            "uptime_seconds": 3600
        }
        req = BeaconRequest(**data)
        
        assert req.agent_id == "abc123"
        assert req.uptime_seconds == 3600
        assert req.last_task_id is None
    
    def test_beacon_with_last_task(self):
        """Test: BeaconRequest avec last_task_id"""
        data = {
            "agent_id": "abc123",
            "api_key": "def456",
            "status": "online",
            "uptime_seconds": 3600,
            "last_task_id": "task-xyz"
        }
        req = BeaconRequest(**data)
        
        assert req.last_task_id == "task-xyz"


class TestTaskCreateRequest:
    """Tests pour le modèle TaskCreateRequest"""
    
    def test_valid_task_request(self):
        """Test: TaskCreateRequest valide"""
        data = {
            "command": "Get-Service",
            "parameters": {"name": "*"},
            "priority": 1
        }
        req = TaskCreateRequest(**data)
        
        assert req.command == "Get-Service"
        assert req.priority == 1
    
    def test_default_priority(self):
        """Test: Priority par défaut à 0"""
        data = {
            "command": "Get-Service"
        }
        req = TaskCreateRequest(**data)
        
        assert req.priority == 0
        assert req.parameters is None


class TestAuditResultRequest:
    """Tests pour le modèle AuditResultRequest"""
    
    def test_valid_result_request_dict(self):
        """Test: AuditResultRequest avec résultat dict"""
        data = {
            "agent_id": "agent-1",
            "api_key": "key-1",
            "task_id": "task-1",
            "status": "success",
            "result": {"services": ["svc1", "svc2"]},
            "execution_time_ms": 1250
        }
        req = AuditResultRequest(**data)
        
        assert req.status == "success"
        assert isinstance(req.result, dict)
    
    def test_valid_result_request_string(self):
        """Test: AuditResultRequest avec résultat string (PowerShell output)"""
        data = {
            "agent_id": "agent-1",
            "api_key": "key-1",
            "task_id": "task-1",
            "status": "success",
            "result": "Status   Name               DisplayName\n---      ----               -----------\nRunning  AdobeARMservice    Adobe Acrobat Update Service",
            "execution_time_ms": 1250
        }
        req = AuditResultRequest(**data)
        
        assert req.status == "success"
        assert isinstance(req.result, str)
    
    def test_result_with_error_message(self):
        """Test: AuditResultRequest avec message d'erreur"""
        data = {
            "agent_id": "agent-1",
            "api_key": "key-1",
            "task_id": "task-1",
            "status": "failed",
            "result": "Error occurred",
            "execution_time_ms": 500,
            "error_message": "Command execution failed"
        }
        req = AuditResultRequest(**data)
        
        assert req.status == "failed"
        assert req.error_message == "Command execution failed"


class TestAgent:
    """Tests pour le modèle Agent"""
    
    def test_valid_agent(self):
        """Test: Créer un Agent valide"""
        agent = Agent(
            agent_id="agent-1",
            api_key="key-1",
            agent_name="test-agent",
            os_version="Windows 10",
            hostname="DESKTOP",
            username="admin",
            created_at=datetime.now()
        )
        
        assert agent.agent_id == "agent-1"
        assert agent.status == AgentStatus.ACTIVE
        assert agent.last_beacon is None
    
    def test_agent_status_enum(self):
        """Test: Les valeurs enum de status sont valides"""
        agent = Agent(
            agent_id="agent-1",
            api_key="key-1",
            agent_name="test-agent",
            os_version="Windows 10",
            hostname="DESKTOP",
            username="admin",
            status=AgentStatus.INACTIVE,
            created_at=datetime.now()
        )
        
        assert agent.status == AgentStatus.INACTIVE


class TestAuditTemplate:
    """Tests pour les configurations d'audit"""

    def test_valid_audit_template_request(self):
        """Test: une configuration d'audit accepte plusieurs commandes PowerShell"""
        data = {
            "name": "Audit système",
            "description": "Vérification de base du système",
            "commands": ["Get-Service", "Get-Process", "Get-LocalUser"],
            "created_by": "admin"
        }
        req = AuditTemplateCreateRequest(**data)

        assert req.name == "Audit système"
        assert len(req.commands) == 3
        assert req.commands[0] == "Get-Service"

    def test_valid_audit_template_response(self):
        """Test: la réponse stockée contient un identifiant et la liste de commandes"""
        template = AuditTemplate(
            template_id="tpl-1",
            name="Audit réseau",
            description="Vérification réseau",
            commands=["Get-NetAdapter", "Get-Process"],
            created_by="admin",
            created_at=datetime.now(),
            enabled=True
        )

        assert template.template_id == "tpl-1"
        assert template.enabled is True
        assert template.commands == ["Get-NetAdapter", "Get-Process"]


class TestPowerShellCommand:
    """Tests pour la bibliothèque de commandes PowerShell"""

    def test_valid_custom_command(self):
        """Test: une commande PowerShell custom peut être créée"""
        data = {
            "name": "Get-ADUserCustom",
            "description": "Retourne les utilisateurs AD",
            "script": "Get-ADUser -Filter * | Select-Object Name, SamAccountName",
            "created_by": "admin"
        }
        req = PowerShellCommandCreateRequest(**data)

        assert req.name == "Get-ADUserCustom"
        assert req.script.startswith("Get-ADUser")

    def test_custom_command_definition(self):
        """Test: le modèle de persistence stocke le code et le nom"""
        command = PowerShellCommandDefinition(
            command_id="cmd-1",
            name="Get-ADUserCustom",
            description="Retourne les utilisateurs AD",
            script="Get-ADUser -Filter * | Select-Object Name, SamAccountName",
            created_by="admin",
            created_at=datetime.now(),
            enabled=True
        )

        assert command.command_id == "cmd-1"
        assert command.name == "Get-ADUserCustom"
        assert "Get-ADUser" in command.script


class TestTask:
    """Tests pour le modèle Task"""
    
    def test_valid_task(self):
        """Test: Créer une Task valide"""
        task = Task(
            task_id="task-1",
            agent_id="agent-1",
            command="Get-Service",
            priority=1,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        assert task.task_id == "task-1"
        assert task.status == TaskStatus.PENDING
        assert task.timeout_seconds == 300  # valeur par défaut
    
    def test_task_status_transitions(self):
        """Test: Les transitions de status sont valides"""
        task = Task(
            task_id="task-1",
            agent_id="agent-1",
            command="Get-Service",
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        # Vérifier que tous les status existent
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.ASSIGNED.value == "assigned"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"


class TestAuditResult:
    """Tests pour le modèle AuditResult"""
    
    def test_valid_audit_result(self):
        """Test: Créer un AuditResult valide"""
        result = AuditResult(
            result_id="result-1",
            task_id="task-1",
            agent_id="agent-1",
            status="success",
            result={"data": "test"},
            execution_time_ms=1250,
            created_at=datetime.now()
        )
        
        assert result.result_id == "result-1"
        assert result.status == "success"
        assert result.error_message is None
    
    def test_audit_result_with_error(self):
        """Test: AuditResult avec erreur"""
        result = AuditResult(
            result_id="result-1",
            task_id="task-1",
            agent_id="agent-1",
            status="failed",
            result="Error output",
            execution_time_ms=500,
            error_message="Command failed",
            created_at=datetime.now()
        )
        
        assert result.status == "failed"
        assert result.error_message == "Command failed"


class TestAuditTemplateDatabase:
    """Tests pour les opérations d'administration des templates"""

    def test_template_update_duplicate_and_history(self):
        """Test: mise à jour, duplication et historique de template"""
        db = Database()

        template = db.create_audit_template(
            name="Audit réseau",
            description="Base",
            commands=["Get-Service", "Get-Process"],
            created_by="admin"
        )

        updated = db.update_audit_template(
            template.template_id,
            name="Audit réseau renforcé",
            description="Version mise à jour",
            commands=["Get-Service", "Get-Process", "Get-IPConfig"],
            created_by="admin"
        )

        duplicate = db.duplicate_audit_template(template.template_id)
        assert updated.name == "Audit réseau renforcé"
        assert duplicate.template_id != template.template_id
        assert duplicate.commands == ["Get-Service", "Get-Process", "Get-IPConfig"]

        db.record_template_application(template.template_id, "agent-42", 3)
        history = db.get_template_history()
        assert len(history) >= 1
        assert history[0]["agent_id"] == "agent-42"

        deleted = db.delete_audit_template(duplicate.template_id)
        assert deleted is True

    def test_apply_template_to_all_agents(self):
        """Test: un template peut être appliqué à tous les agents"""
        db = Database()

        db.create_agent("agent-a", "Windows 11", "A", "admin")
        db.create_agent("agent-b", "Windows 11", "B", "admin")

        template = db.create_audit_template(
            name="Audit global",
            description="Tous les agents",
            commands=["Get-Process", "Get-Service"],
            created_by="admin"
        )

        result = db.apply_template_to_all_agents(template.template_id)
        assert result["agents_total"] == 2
        assert result["task_count"] == 4
        assert len(db.list_tasks()) >= 4


class TestEnumValues:
    """Tests pour les énums"""
    
    def test_agent_status_values(self):
        """Test: Toutes les valeurs de AgentStatus"""
        assert AgentStatus.ACTIVE.value == "active"
        assert AgentStatus.INACTIVE.value == "inactive"
        assert AgentStatus.COMPROMISED.value == "compromised"
    
    def test_task_status_values(self):
        """Test: Toutes les valeurs de TaskStatus"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.ASSIGNED.value == "assigned"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
