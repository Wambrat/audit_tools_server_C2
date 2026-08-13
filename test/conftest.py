"""
Fixtures pytest partagées pour tous les tests.
Initialise les dépendances communes (mock DB, logger, etc.)
"""
import pytest
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules de l'app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Database
from app.rate_limiter import RateLimiter
from app.logger import get_logger
from app.db import set_db_instance
from app.models import Agent, Task, AuditResult, BeaconHistory, TaskStatus


@pytest.fixture
def mock_db():
    """Fixture pour une instance de Database vierge"""
    db = Database()
    set_db_instance(db)  # Set comme DB globale
    yield db
    # Cleanup après le test
    set_db_instance(None)


@pytest.fixture
def rate_limiter():
    """Fixture pour une instance de RateLimiter vierge"""
    return RateLimiter()


@pytest.fixture
def logger():
    """Fixture pour le logger"""
    return get_logger("test")


@pytest.fixture
def sample_agent_data():
    """Données d'exemple pour un agent"""
    return {
        "agent_name": "test-agent-001",
        "os_version": "Windows 10 22H2",
        "hostname": "DESKTOP-TEST",
        "username": "admin"
    }


@pytest.fixture
def sample_task_data():
    """Données d'exemple pour une tâche"""
    return {
        "command": "Get-Service",
        "parameters": {"name": "*"},
        "priority": 1,
        "timeout_seconds": 300
    }


@pytest.fixture
def sample_result_data():
    """Données d'exemple pour un résultat"""
    return {
        "status": "success",
        "result": {"services": ["svchost", "WinRM", "LogonUI"]},
        "execution_time_ms": 1250,
        "error_message": None
    }
