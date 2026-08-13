"""
Tests for CSRF Protection

Tests for cross-site request forgery prevention:
- Token generation
- Token validation
- Token expiration
- Session matching
- Token cleanup

Run with: pytest test/test_csrf.py -v
"""

import pytest
import os
from unittest.mock import patch
from app.csrf import CSRFProtection, get_csrf_protection
from datetime import datetime, timedelta
import time


class TestCSRFTokenGeneration:
    """Tests for CSRF token generation"""
    
    def test_csrf_token_generated(self):
        """Test that CSRF token is generated"""
        csrf = CSRFProtection(secret_key="test_secret_key")
        session_id = "session_123"
        
        token = csrf.generate_token(session_id)
        
        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)
    
    def test_csrf_token_unique(self):
        """Test that each generated token is unique"""
        csrf = CSRFProtection(secret_key="test_secret_key")
        session_id = "session_123"
        
        token1 = csrf.generate_token(session_id)
        token2 = csrf.generate_token(session_id)
        
        assert token1 != token2
    
    def test_csrf_token_different_sessions(self):
        """Test tokens from different sessions are different"""
        csrf = CSRFProtection(secret_key="test_secret_key")
        
        token1 = csrf.generate_token("session_1")
        token2 = csrf.generate_token("session_2")
        
        assert token1 != token2
    
    def test_csrf_token_hex_format(self):
        """Test that CSRF token is in hex format"""
        csrf = CSRFProtection(secret_key="test_secret_key")
        token = csrf.generate_token("session_123")
        
        # Should be valid hex string
        int(token, 16)  # Will raise ValueError if not valid hex


class TestCSRFTokenValidation:
    """Tests for CSRF token validation"""
    
    def test_csrf_token_validation_success(self):
        """Test successful token validation"""
        csrf = CSRFProtection(secret_key="test_secret_key")
        session_id = "session_123"
        
        token = csrf.generate_token(session_id)
        is_valid, error = csrf.validate_token(token, session_id)
        
        assert is_valid is True
        assert error is None
    
    def test_csrf_token_validation_missing(self):
        """Test validation fails with missing token"""
        csrf = CSRFProtection(secret_key="test_secret_key")
        
        is_valid, error = csrf.validate_token("", "session_123")
        
        assert is_valid is False
        assert "missing" in error.lower()
    
    def test_csrf_token_validation_invalid(self):
        """Test validation fails with invalid token"""
        csrf = CSRFProtection(secret_key="test_secret_key")
        
        is_valid, error = csrf.validate_token("invalid_token_12345", "session_123")
        
        assert is_valid is False
        assert "invalid" in error.lower() or "expired" in error.lower()
    
    def test_csrf_token_validation_session_mismatch(self):
        """Test validation fails with mismatched session"""
        csrf = CSRFProtection(secret_key="test_secret_key")
        
        token = csrf.generate_token("session_123")
        is_valid, error = csrf.validate_token(token, "session_999")
        
        assert is_valid is False
        assert "mismatch" in error.lower() or "session" in error.lower()
    
    def test_csrf_token_validation_expired(self):
        """Test validation fails with expired token"""
        csrf = CSRFProtection(secret_key="test_secret_key", token_lifetime_hours=0)
        session_id = "session_123"
        
        token = csrf.generate_token(session_id)
        
        # Wait for token to expire
        time.sleep(0.1)
        
        is_valid, error = csrf.validate_token(token, session_id)
        
        assert is_valid is False
        assert "expired" in error.lower()


class TestCSRFTokenCleanup:
    """Tests for CSRF token cleanup"""
    
    def test_csrf_token_cleanup(self):
        """Test expired tokens are cleaned up"""
        csrf = CSRFProtection(secret_key="test_secret_key", token_lifetime_hours=0)
        session_id = "session_123"
        
        # Generate token
        token = csrf.generate_token(session_id)
        assert token in csrf.tokens
        
        # Wait for expiration
        time.sleep(0.1)
        
        # Cleanup
        removed = csrf.cleanup_expired_tokens()
        
        assert removed == 1
        assert token not in csrf.tokens
    
    def test_csrf_token_cleanup_valid_preserved(self):
        """Test valid tokens are not cleaned up"""
        csrf = CSRFProtection(secret_key="test_secret_key", token_lifetime_hours=24)
        
        token1 = csrf.generate_token("session_1")
        token2 = csrf.generate_token("session_2")
        
        removed = csrf.cleanup_expired_tokens()
        
        # No tokens should be expired
        assert removed == 0
        assert token1 in csrf.tokens
        assert token2 in csrf.tokens


class TestCSRFSingleton:
    """Tests for CSRF protection singleton"""
    
    def test_csrf_protection_singleton(self):
        """Test get_csrf_protection returns same instance"""
        csrf1 = get_csrf_protection()
        csrf2 = get_csrf_protection()
        
        assert csrf1 is csrf2
    
    def test_csrf_protection_initialization(self):
        """Test CSRF protection requires secret key"""
        # Should not raise with valid secret
        with patch.dict(os.environ, {'ADMIN_SECRET_KEY': 'test_secret'}):
            csrf = CSRFProtection()
            assert csrf is not None


class TestCSRFIntegration:
    """Integration tests for CSRF flow"""
    
    def test_csrf_full_flow(self):
        """Test complete CSRF token flow: generate, validate, expire"""
        csrf = CSRFProtection(secret_key="test_secret_key", token_lifetime_hours=24)
        session_id = "user_session_abc123"
        
        # Step 1: Generate token
        token = csrf.generate_token(session_id)
        assert len(token) > 0
        
        # Step 2: Validate token immediately (should succeed)
        is_valid, error = csrf.validate_token(token, session_id)
        assert is_valid is True
        assert error is None
        
        # Step 3: Try to use token again (should still succeed)
        is_valid, error = csrf.validate_token(token, session_id)
        assert is_valid is True
        assert error is None
        
        # Step 4: Try with wrong session (should fail)
        is_valid, error = csrf.validate_token(token, "wrong_session")
        assert is_valid is False
    
    def test_csrf_multiple_sessions(self):
        """Test CSRF tokens work independently for multiple sessions"""
        csrf = CSRFProtection(secret_key="test_secret_key")
        
        # Create tokens for different sessions
        token1 = csrf.generate_token("session_1")
        token2 = csrf.generate_token("session_2")
        
        # Each token should only validate for its own session
        assert csrf.validate_token(token1, "session_1")[0] is True
        assert csrf.validate_token(token2, "session_2")[0] is True
        assert csrf.validate_token(token1, "session_2")[0] is False
        assert csrf.validate_token(token2, "session_1")[0] is False


class TestCSRFConfiguration:
    """Tests for CSRF configuration"""
    
    def test_csrf_custom_lifetime(self):
        """Test custom token lifetime"""
        csrf = CSRFProtection(
            secret_key="test_secret_key",
            token_lifetime_hours=1
        )
        
        assert csrf.token_lifetime_hours == 1
    
    def test_csrf_secret_from_env(self):
        """Test CSRF uses secret from environment"""
        with patch.dict(os.environ, {'CSRF_SECRET_KEY': 'env_secret_key'}):
            csrf = CSRFProtection()
            assert csrf.secret_key == b'env_secret_key'
    
    def test_csrf_falls_back_to_admin_secret(self):
        """Test CSRF falls back to ADMIN_SECRET_KEY"""
        with patch.dict(os.environ, {'ADMIN_SECRET_KEY': 'admin_secret_key'}, clear=False):
            # Remove CSRF_SECRET_KEY if it exists
            if 'CSRF_SECRET_KEY' in os.environ:
                del os.environ['CSRF_SECRET_KEY']
            csrf = CSRFProtection()
            # Should use ADMIN_SECRET_KEY as fallback
            assert csrf.secret_key is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
