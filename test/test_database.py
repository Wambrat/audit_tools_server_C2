"""
Tests unitaires pour app/database.py
Teste le stockage en mÃ©moire des agents, tÃ¢ches, et rÃ©sultats
"""
import pytest
from datetime import datetime
from app.database import Database
from app.models import AgentStatus, TaskStatus


class TestDatabaseAgents:
    """Tests pour les opÃ©rations d'agents"""
    
    def test_create_agent(self, sample_agent_data):
        """Test: CrÃ©er un agent"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        
        assert agent.agent_id is not None
        assert agent.api_key is not None
        assert agent.agent_name == sample_agent_data["agent_name"]
        assert agent.status == AgentStatus.ACTIVE
        assert agent.created_at is not None
    
    def test_get_agent(self, sample_agent_data):
        """Test: RÃ©cupÃ©rer un agent par ID"""
        db = Database()
        created_agent = db.create_agent(**sample_agent_data)
        
        retrieved_agent = db.get_agent(created_agent.agent_id)
        
        assert retrieved_agent is not None
        assert retrieved_agent.agent_id == created_agent.agent_id
        assert retrieved_agent.agent_name == sample_agent_data["agent_name"]
    
    def test_get_nonexistent_agent(self):
        """Test: RÃ©cupÃ©rer un agent inexistant"""
        db = Database()
        agent = db.get_agent("nonexistent-id")
        
        assert agent is None
    
    def test_authenticate_agent_valid(self, sample_agent_data):
        """Test: Authentifier un agent avec credentials valides"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        
        is_valid = db.authenticate_agent(agent.agent_id, agent.api_key)
        
        assert is_valid is True
    
    def test_authenticate_agent_invalid_key(self, sample_agent_data):
        """Test: Rejet avec mauvaise API key"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        
        is_valid = db.authenticate_agent(agent.agent_id, "wrong-key")
        
        assert is_valid is False
    
    def test_authenticate_nonexistent_agent(self):
        """Test: Authentifier un agent inexistant"""
        db = Database()
        is_valid = db.authenticate_agent("nonexistent", "any-key")
        
        assert is_valid is False
    
    def test_update_agent_beacon(self, sample_agent_data):
        """Test: Mettre Ã  jour le timestamp du dernier beacon"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        
        assert agent.last_beacon is None
        
        db.update_agent_beacon(agent.agent_id)
        
        updated_agent = db.get_agent(agent.agent_id)
        assert updated_agent.last_beacon is not None
    
    def test_list_agents(self, sample_agent_data):
        """Test: Lister tous les agents"""
        db = Database()
        
        db.create_agent(**sample_agent_data)
        db.create_agent("agent-2", "Windows 11", "DESKTOP2", "user")
        db.create_agent("agent-3", "Linux", "LAPTOP", "root")
        
        agents = db.list_agents()
        
        assert len(agents) == 3
        assert all(a.status == AgentStatus.ACTIVE for a in agents)


class TestDatabaseTasks:
    """Tests pour les opÃ©rations de tÃ¢ches"""
    
    def test_create_task(self, sample_agent_data, sample_task_data):
        """Test: CrÃ©er une tÃ¢che"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        
        task = db.create_task(agent.agent_id, **sample_task_data)
        
        assert task.task_id is not None
        assert task.agent_id == agent.agent_id
        assert task.command == sample_task_data["command"]
        assert task.status == TaskStatus.PENDING
    
    def test_get_task(self, sample_agent_data, sample_task_data):
        """Test: RÃ©cupÃ©rer une tÃ¢che par ID"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        created_task = db.create_task(agent.agent_id, **sample_task_data)
        
        retrieved_task = db.get_task(created_task.task_id)
        
        assert retrieved_task is not None
        assert retrieved_task.task_id == created_task.task_id
    
    def test_get_nonexistent_task(self):
        """Test: RÃ©cupÃ©rer une tÃ¢che inexistante"""
        db = Database()
        task = db.get_task("nonexistent-id")
        
        assert task is None
    
    def test_get_pending_tasks(self, sample_agent_data, sample_task_data):
        """Test: RÃ©cupÃ©rer les tÃ¢ches en attente d'un agent"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        
        # CrÃ©er 3 tÃ¢ches
        task1 = db.create_task(agent.agent_id, "Command1", priority=1)
        task2 = db.create_task(agent.agent_id, "Command2", priority=2)
        task3 = db.create_task(agent.agent_id, "Command3", priority=0)
        
        pending_tasks = db.get_pending_tasks(agent.agent_id)
        
        assert len(pending_tasks) == 3
        # Doivent Ãªtre triÃ©es par prioritÃ© (dÃ©croissante) puis par date
        assert pending_tasks[0].priority == 2
        assert pending_tasks[1].priority == 1
        assert pending_tasks[2].priority == 0
    
    def test_mark_task_assigned(self, sample_agent_data, sample_task_data):
        """Test: Marquer une tÃ¢che comme assignÃ©e"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        task = db.create_task(agent.agent_id, **sample_task_data)
        
        db.mark_task_assigned(task.task_id)
        
        updated_task = db.get_task(task.task_id)
        assert updated_task.status == TaskStatus.ASSIGNED
        assert updated_task.assigned_at is not None
    
    def test_list_tasks_all(self, sample_agent_data):
        """Test: Lister toutes les tÃ¢ches"""
        db = Database()
        agent1 = db.create_agent(**sample_agent_data)
        agent2 = db.create_agent("agent-2", "Windows", "Pjadus", "user")
        
        db.create_task(agent1.agent_id, "Command1")
        db.create_task(agent1.agent_id, "Command2")
        db.create_task(agent2.agent_id, "Command3")
        
        all_tasks = db.list_tasks()
        
        assert len(all_tasks) == 3
    
    def test_list_tasks_by_agent(self, sample_agent_data):
        """Test: Lister les tÃ¢ches d'un agent"""
        db = Database()
        agent1 = db.create_agent(**sample_agent_data)
        agent2 = db.create_agent("agent-2", "Windows", "Pjadus", "user")
        
        db.create_task(agent1.agent_id, "Command1")
        db.create_task(agent1.agent_id, "Command2")
        db.create_task(agent2.agent_id, "Command3")
        
        agent1_tasks = db.list_tasks(agent1.agent_id)
        
        assert len(agent1_tasks) == 2
        assert all(t.agent_id == agent1.agent_id for t in agent1_tasks)


class TestDefaultModuleSeed:
    """Tests pour l'initialisation des modules par dÃ©faut depuis l'archive zip"""

    def test_seed_default_modules(self):
        """Test: importer les modules standards depuis modules.zip pour la commande et les templates"""
        db = Database()

        inserted = db.seed_default_modules()

        assert inserted["commands"] > 0
        assert inserted["templates"] > 0
        assert any(cmd.name == "Get-ADPolPassAudit" for cmd in db.list_powershell_commands())
        assert any(t.name == "Audit Complet (toutes fonctions)" for t in db.list_audit_templates())
        assert any(t.name for t in db.list_audit_templates())

    def test_template_tasks_include_registered_command_script(self):
        """Test: les tÃ¢ches gÃ©nÃ©rÃ©es depuis un template doivent inclure le script enregistrÃ© pour le command"""
        db = Database()
        agent = db.create_agent("agent-a", "Windows 11", "HOSTA", "admin")
        db.create_powershell_command(
            name="Get-FirewallAudit",
            description="Audit firewall",
            script="function Get-FirewallAudit { 'firewall ok' }",
            created_by="system",
        )
        template = db.create_audit_template(
            name="Audit firewall",
            description="Template de test",
            commands=["Get-FirewallAudit"],
            created_by="admin",
        )

        tasks = db.build_tasks_from_template(template.template_id, agent.agent_id)

        assert len(tasks) == 1
        assert tasks[0].parameters is not None
        assert tasks[0].parameters["script"] == "function Get-FirewallAudit { 'firewall ok' }"


class TestDatabaseResults:
    """Tests pour les opÃ©rations de rÃ©sultats"""
    
    def test_store_result_success(self, sample_agent_data, sample_task_data, sample_result_data):
        """Test: Stocker un rÃ©sultat avec succÃ¨s"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        task = db.create_task(agent.agent_id, **sample_task_data)
        
        result = db.store_result(
            task_id=task.task_id,
            agent_id=agent.agent_id,
            **sample_result_data
        )
        
        assert result.result_id is not None
        assert result.task_id == task.task_id
        assert result.status == "success"
        assert result.created_at is not None
    
    def test_store_result_updates_task_status(self, sample_agent_data, sample_task_data):
        """Test: Stocker un rÃ©sultat met Ã  jour le statut de la tÃ¢che"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        task = db.create_task(agent.agent_id, **sample_task_data)
        
        db.store_result(
            task_id=task.task_id,
            agent_id=agent.agent_id,
            status="success",
            result={"data": "test"},
            execution_time_ms=1000
        )
        
        updated_task = db.get_task(task.task_id)
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.completed_at is not None
    
    def test_store_result_failed_updates_task(self, sample_agent_data, sample_task_data):
        """Test: Un rÃ©sultat Ã©chouÃ© marque la tÃ¢che comme FAILED"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        task = db.create_task(agent.agent_id, **sample_task_data)
        
        db.store_result(
            task_id=task.task_id,
            agent_id=agent.agent_id,
            status="failed",
            result="Error occurred",
            execution_time_ms=500,
            error_message="Command failed"
        )
        
        updated_task = db.get_task(task.task_id)
        assert updated_task.status == TaskStatus.FAILED
    
    def test_get_result(self, sample_agent_data, sample_task_data):
        """Test: RÃ©cupÃ©rer un rÃ©sultat par ID"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        task = db.create_task(agent.agent_id, **sample_task_data)
        
        stored_result = db.store_result(
            task_id=task.task_id,
            agent_id=agent.agent_id,
            status="success",
            result={"data": "test"},
            execution_time_ms=1000
        )
        
        retrieved_result = db.get_result(stored_result.result_id)
        
        assert retrieved_result is not None
        assert retrieved_result.result_id == stored_result.result_id
    
    def test_list_results_all(self, sample_agent_data, sample_task_data):
        """Test: Lister tous les rÃ©sultats"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        
        task1 = db.create_task(agent.agent_id, **sample_task_data)
        task2 = db.create_task(agent.agent_id, "Command2")
        
        db.store_result(task1.task_id, agent.agent_id, "success", {"data": "1"}, 1000)
        db.store_result(task2.task_id, agent.agent_id, "success", {"data": "2"}, 1500)
        
        # RÃ©cupÃ©rer tous les rÃ©sultats en utilisant get_results_by_agent
        all_results = db.get_results_by_agent(agent.agent_id)
        
        assert len(all_results) == 2
    
    def test_list_results_by_agent(self, sample_agent_data, sample_task_data):
        """Test: Lister les rÃ©sultats d'un agent"""
        db = Database()
        agent1 = db.create_agent(**sample_agent_data)
        agent2 = db.create_agent("agent-2", "Windows", "Pjadus", "user")
        
        task1 = db.create_task(agent1.agent_id, **sample_task_data)
        task2 = db.create_task(agent2.agent_id, **sample_task_data)
        
        db.store_result(task1.task_id, agent1.agent_id, "success", {"data": "1"}, 1000)
        db.store_result(task2.task_id, agent2.agent_id, "success", {"data": "2"}, 1000)
        
        agent1_results = db.get_results_by_agent(agent1.agent_id)
        
        assert len(agent1_results) == 1
        assert agent1_results[0].agent_id == agent1.agent_id


class TestDatabaseBeaconHistory:
    """Tests pour l'historique des beacons"""
    
    def test_record_beacon(self, sample_agent_data):
        """Test: Enregistrer un beacon"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        
        beacon = db.record_beacon(
            agent_id=agent.agent_id,
            beacon_status="online",
            uptime_seconds=3600,
            tasks_count=1
        )
        
        assert beacon.agent_id == agent.agent_id
        assert beacon.beacon_status == "online"
        assert beacon.created_at is not None
    
    def test_get_beacon_history(self, sample_agent_data):
        """Test: RÃ©cupÃ©rer l'historique des beacons"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        
        db.record_beacon(agent.agent_id, "online", 1000, 0)
        db.record_beacon(agent.agent_id, "online", 2000, 1)
        db.record_beacon(agent.agent_id, "online", 2500, 2)
        
        history = db.get_beacon_history(agent.agent_id)
        
        assert len(history) >= 3
        assert all(b.agent_id == agent.agent_id for b in history)
    
    def test_get_beacon_stats(self, sample_agent_data):
        """Test: Obtenir les statistiques de beacon"""
        db = Database()
        agent = db.create_agent(**sample_agent_data)
        
        db.record_beacon(agent.agent_id, "online", 1000, 0)
        db.record_beacon(agent.agent_id, "online", 2000, 1)
        
        stats = db.get_beacon_stats(agent.agent_id)
        
        assert stats["agent_id"] == agent.agent_id
        assert stats["total_beacons"] == 2
        assert stats["avg_uptime_seconds"] == 1500


class TestDatabaseIntegration:
    """Tests d'intÃ©gration complets"""
    
    def test_full_workflow(self, sample_agent_data, sample_task_data):
        """Test: Workflow complet (enroll â†’ beacon â†’ task â†’ result)"""
        db = Database()
        
        # 1. Enroll
        agent = db.create_agent(**sample_agent_data)
        assert agent.agent_id is not None
        
        # 2. Beacon
        db.update_agent_beacon(agent.agent_id)
        db.record_beacon(agent.agent_id, "online", 100, 0)
        
        # 3. Create task
        task = db.create_task(agent.agent_id, **sample_task_data)
        pending = db.get_pending_tasks(agent.agent_id)
        assert len(pending) == 1
        
        # 4. Mark assigned
        db.mark_task_assigned(task.task_id)
        assert db.get_task(task.task_id).status == TaskStatus.ASSIGNED
        
        # 5. Submit result
        result = db.store_result(
            task_id=task.task_id,
            agent_id=agent.agent_id,
            status="success",
            result={"services": ["svc1", "svjadus"]},
            execution_time_ms=1250
        )
        
        # Verify completion
        assert db.get_task(task.task_id).status == TaskStatus.COMPLETED
        assert db.get_result(result.result_id) is not None
        assert len(db.get_results_by_agent(agent.agent_id)) == 1

