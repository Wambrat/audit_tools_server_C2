"""
Tests unitaires pour app/auth.py
Teste la vérification des credentials des agents
"""
import pytest
from fastapi import HTTPException, status
from app.auth import verify_agent_credentials
from app.models import AgentStatus


class TestVerifyAgentCredentials:
    """Tests pour la fonction verify_agent_credentials"""
    
    def test_valid_credentials(self, mock_db, sample_agent_data):
        """Test: Vérification avec des credentials valides"""
        # Setup: Créer un agent
        agent = mock_db.create_agent(**sample_agent_data)
        
        # Act: Vérifier les credentials
        result = verify_agent_credentials(agent.agent_id, agent.api_key)
        
        # Assert
        assert result is not None
        assert result.agent_id == agent.agent_id
        assert result.agent_name == sample_agent_data["agent_name"]
        assert result.status == AgentStatus.ACTIVE
    
    def test_invalid_agent_id(self, mock_db):
        """Test: Rejet avec agent_id invalide"""
        with pytest.raises(HTTPException) as exc_info:
            verify_agent_credentials("invalid-agent-id", "any-key")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid agent credentials" in exc_info.value.detail
    
    def test_invalid_api_key(self, mock_db, sample_agent_data):
        """Test: Rejet avec api_key invalide"""
        # Setup: Créer un agent
        agent = mock_db.create_agent(**sample_agent_data)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            verify_agent_credentials(agent.agent_id, "wrong-api-key")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_missing_agent_id(self, mock_db):
        """Test: Rejet avec agent_id vide"""
        with pytest.raises(HTTPException) as exc_info:
            verify_agent_credentials("", "any-key")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing agent credentials" in exc_info.value.detail
    
    def test_missing_api_key(self, mock_db, sample_agent_data):
        """Test: Rejet avec api_key vide"""
        agent = mock_db.create_agent(**sample_agent_data)
        
        with pytest.raises(HTTPException) as exc_info:
            verify_agent_credentials(agent.agent_id, "")
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_none_credentials(self, mock_db):
        """Test: Rejet avec credentials None"""
        with pytest.raises(HTTPException):
            verify_agent_credentials(None, None)
    
    def test_case_sensitivity(self, mock_db, sample_agent_data):
        """Test: Les IDs sont sensibles à la casse"""
        agent = mock_db.create_agent(**sample_agent_data)
        original_id = agent.agent_id
        
        # Essayer avec une majuscule différente
        with pytest.raises(HTTPException):
            verify_agent_credentials(original_id.upper(), agent.api_key)
