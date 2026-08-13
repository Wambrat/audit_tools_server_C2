"""
Tests for Session Management & Key Rotation

Tests for secure session management and key rotation including:
- Session lifecycle (create, validate, regenerate, invalidate)
- Session expiration
- Key rotation with history tracking
- Key cleanup and retention
- Session security validation

Run with: pytest test/test_session_management.py -v
"""

import pytest
from datetime import datetime, timedelta
from app.session_management import (
    SessionManager, KeyRotationManager, SessionSecurityValidator,
    SessionStatus, get_session_manager, get_key_rotation_manager
)


class TestSessionCreation:
    """Tests for session creation"""
    
    @pytest.fixture
    def manager(self):
        """Get session manager"""
        return SessionManager()
    
    def test_create_session(self, manager):
        """Test creating a new session"""
        session = manager.create_session("user123", "192.168.1.1", "Mozilla/5.0")
        
        assert session.user_id == "user123"
        assert session.status == SessionStatus.ACTIVE
        assert session.ip_address == "192.168.1.1"
        assert session.user_agent == "Mozilla/5.0"
    
    def test_session_id_unique(self, manager):
        """Test session IDs are unique"""
        session1 = manager.create_session("user1", "192.168.1.1", "UA1")
        session2 = manager.create_session("user2", "192.168.1.2", "UA2")
        
        assert session1.session_id != session2.session_id
    
    def test_session_expiration_time(self, manager):
        """Test session has expiration time"""
        manager.session_timeout_minutes = 60
        session = manager.create_session("user", "127.0.0.1", "UA")
        
        created = datetime.fromisoformat(session.created_at)
        expires = datetime.fromisoformat(session.expires_at)
        diff_minutes = (expires - created).total_seconds() / 60
        
        assert diff_minutes == 60


class TestSessionValidation:
    """Tests for session validation"""
    
    @pytest.fixture
    def manager(self):
        """Get session manager"""
        return SessionManager()
    
    def test_validate_active_session(self, manager):
        """Test validating active session"""
        session = manager.create_session("user", "127.0.0.1", "UA")
        is_valid, error = manager.validate_session(session.session_id)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_nonexistent_session(self, manager):
        """Test validating nonexistent session"""
        is_valid, error = manager.validate_session("fake-session-id")
        
        assert is_valid is False
        assert "not found" in error.lower()
    
    def test_validate_expired_session(self, manager):
        """Test validating expired session"""
        session = manager.create_session("user", "127.0.0.1", "UA")
        
        # Manually expire the session
        past = datetime.now() - timedelta(hours=1)
        session.expires_at = past.isoformat()
        
        is_valid, error = manager.validate_session(session.session_id)
        
        assert is_valid is False
        assert "expired" in error.lower()
    
    def test_validate_invalidated_session(self, manager):
        """Test validating invalidated session"""
        session = manager.create_session("user", "127.0.0.1", "UA")
        manager.invalidate_session(session.session_id)
        
        is_valid, error = manager.validate_session(session.session_id)
        
        assert is_valid is False
        assert "invalidated" in error.lower()


class TestSessionRegeneration:
    """Tests for session regeneration"""
    
    @pytest.fixture
    def manager(self):
        """Get session manager"""
        return SessionManager()
    
    def test_regenerate_session(self, manager):
        """Test regenerating a session"""
        old_session = manager.create_session("user", "192.168.1.1", "UA1")
        new_session = manager.regenerate_session(
            old_session.session_id, "192.168.1.2", "UA2"
        )
        
        assert new_session is not None
        assert new_session.session_id != old_session.session_id
        assert new_session.regenerated_from == old_session.session_id
        assert new_session.ip_address == "192.168.1.2"
        assert new_session.user_agent == "UA2"
    
    def test_old_session_invalidated_on_regeneration(self, manager):
        """Test old session invalidated on regeneration"""
        old_session = manager.create_session("user", "127.0.0.1", "UA")
        manager.regenerate_session(old_session.session_id, "127.0.0.1", "UA")
        
        is_valid, _ = manager.validate_session(old_session.session_id)
        assert is_valid is False
    
    def test_regenerate_nonexistent_session(self, manager):
        """Test regenerating nonexistent session"""
        result = manager.regenerate_session("fake-id", "127.0.0.1", "UA")
        
        assert result is None


class TestSessionInvalidation:
    """Tests for session invalidation"""
    
    @pytest.fixture
    def manager(self):
        """Get session manager"""
        return SessionManager()
    
    def test_invalidate_session(self, manager):
        """Test invalidating a session"""
        session = manager.create_session("user", "127.0.0.1", "UA")
        result = manager.invalidate_session(session.session_id)
        
        assert result is True
        assert manager.sessions[session.session_id].status == SessionStatus.INVALIDATED
    
    def test_invalidate_all_user_sessions(self, manager):
        """Test invalidating all user sessions"""
        session1 = manager.create_session("user1", "127.0.0.1", "UA")
        session2 = manager.create_session("user1", "127.0.0.2", "UA")
        session3 = manager.create_session("user2", "127.0.0.3", "UA")
        
        # Create second session for user1 (overwrites index)
        manager.sessions[session2.session_id] = session2
        
        count = manager.invalidate_all_user_sessions("user1")
        
        assert count >= 2  # At least 2 user1 sessions invalidated


class TestSessionCleanup:
    """Tests for session cleanup"""
    
    @pytest.fixture
    def manager(self):
        """Get session manager"""
        return SessionManager()
    
    def test_cleanup_expired_sessions(self, manager):
        """Test cleanup removes expired sessions"""
        session1 = manager.create_session("user1", "127.0.0.1", "UA")
        session2 = manager.create_session("user2", "127.0.0.1", "UA")
        
        # Manually expire both sessions
        past = datetime.now() - timedelta(hours=1)
        session1.expires_at = past.isoformat()
        session2.expires_at = past.isoformat()
        
        initial_count = len(manager.sessions)
        
        removed = manager.cleanup_expired_sessions()
        
        assert removed == 2
        assert len(manager.sessions) < initial_count
    
    def test_cleanup_preserves_active_sessions(self, manager):
        """Test cleanup preserves active sessions"""
        session = manager.create_session("user", "127.0.0.1", "UA")
        
        removed = manager.cleanup_expired_sessions()
        
        assert removed == 0
        assert session.session_id in manager.sessions


class TestKeyRotation:
    """Tests for key rotation"""
    
    @pytest.fixture
    def manager(self):
        """Get key rotation manager"""
        return KeyRotationManager("key-001")
    
    def test_initial_key(self, manager):
        """Test initial key is set"""
        assert manager.current_key_id == "key-001"
        assert manager.get_current_key_id() == "key-001"
    
    def test_rotate_key(self, manager):
        """Test rotating key"""
        result = manager.rotate_key("key-002", admin_id="admin", reason="Scheduled")
        
        assert result is True
        assert manager.current_key_id == "key-002"
    
    def test_rotation_history(self, manager):
        """Test rotation history is recorded"""
        manager.rotate_key("key-002")
        manager.rotate_key("key-003")
        
        history = manager.get_rotation_history()
        
        assert len(history) == 2
        assert history[0]["new_key_id"] == "key-002"
        assert history[1]["new_key_id"] == "key-003"
    
    def test_can_decrypt_with_current_key(self, manager):
        """Test current key can decrypt"""
        assert manager.can_decrypt_with_key("key-001") is True
    
    def test_can_decrypt_with_old_key(self, manager):
        """Test old key can decrypt (for data encrypted with old key)"""
        manager.rotate_key("key-002")
        
        # Old key should still be available for decryption
        assert manager.can_decrypt_with_key("key-001") is True
        assert manager.can_decrypt_with_key("key-002") is True
    
    def test_cannot_decrypt_with_removed_key(self, manager):
        """Test removed key cannot decrypt"""
        assert manager.can_decrypt_with_key("key-999") is False
    
    def test_get_decryption_keys(self, manager):
        """Test get all decryption keys"""
        manager.rotate_key("key-002")
        
        keys = manager.get_decryption_keys()
        
        assert "key-001" in keys
        assert "key-002" in keys
    
    def test_key_cleanup_retains_limit(self, manager):
        """Test cleanup maintains max key retention"""
        manager.max_active_keys = 2
        
        manager.rotate_key("key-002")
        manager.rotate_key("key-003")
        manager.rotate_key("key-004")
        
        keys = manager.get_decryption_keys()
        
        assert len(keys) <= 2


class TestSessionSecurityValidation:
    """Tests for session security validation"""
    
    def test_validate_same_ip(self):
        """Test validation succeeds for same IP"""
        is_valid, error = SessionSecurityValidator.validate_session_mobility(
            "192.168.1.1", "192.168.1.1"
        )
        
        assert is_valid is True
    
    def test_validate_user_agent_consistency_same(self):
        """Test user agent consistency - same"""
        is_valid, error = SessionSecurityValidator.validate_user_agent_consistency(
            "Mozilla/5.0", "Mozilla/5.0"
        )
        
        assert is_valid is True
    
    def test_validate_user_agent_consistency_different(self):
        """Test user agent consistency - different browser"""
        is_valid, error = SessionSecurityValidator.validate_user_agent_consistency(
            "Mozilla/5.0 (Chrome)", "Safari/5.0"
        )
        
        # Different browser is suspicious
        assert is_valid is False


class TestSessionManagementSingleton:
    """Tests for singleton patterns"""
    
    def test_session_manager_singleton(self):
        """Test SessionManager singleton"""
        manager1 = get_session_manager()
        manager2 = get_session_manager()
        
        assert manager1 is manager2
    
    def test_key_rotation_manager_singleton(self):
        """Test KeyRotationManager singleton"""
        manager1 = get_key_rotation_manager("key-001")
        manager2 = get_key_rotation_manager("key-001")
        
        assert manager1 is manager2


class TestSessionManagementIntegration:
    """Integration tests for session management"""
    
    def test_complete_session_lifecycle(self):
        """Test complete session lifecycle"""
        manager = SessionManager(session_timeout_minutes=30)
        
        # Create session
        session = manager.create_session("user123", "192.168.1.1", "Chrome")
        assert session.status == SessionStatus.ACTIVE
        
        # Validate session
        is_valid, _ = manager.validate_session(session.session_id)
        assert is_valid is True
        
        # Regenerate on privilege escalation
        new_session = manager.regenerate_session(
            session.session_id, "192.168.1.1", "Chrome"
        )
        assert new_session is not None
        
        # Old session now invalid
        is_valid, _ = manager.validate_session(session.session_id)
        assert is_valid is False
        
        # New session valid
        is_valid, _ = manager.validate_session(new_session.session_id)
        assert is_valid is True
    
    def test_complete_key_rotation_lifecycle(self):
        """Test complete key rotation lifecycle"""
        manager = KeyRotationManager("key-001")
        
        # Encrypt with current key
        current = manager.get_current_key_id()
        assert current == "key-001"
        
        # Rotate key
        manager.rotate_key("key-002", admin_id="admin1", reason="Scheduled")
        assert manager.get_current_key_id() == "key-002"
        
        # Old key still available for decryption
        assert manager.can_decrypt_with_key("key-001") is True
        assert manager.can_decrypt_with_key("key-002") is True
        
        # Verify history
        history = manager.get_rotation_history()
        assert len(history) == 1
        assert history[0]["admin_id"] == "admin1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
