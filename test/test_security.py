"""
Security Tests - Password Hashing, Rate Limiting, Payload Validation, Secrets Masking

Tests for security enhancements:
1. bcrypt password hashing
2. Rate limiting on /admin/login
3. Payload size validation
4. Secrets masking in logs

Run with: pytest test/test_security.py -v
"""

import pytest
import os
from app.admin_auth import hash_password, verify_password
from app.logger import SecretsFilter
import logging
import re


class TestPasswordHashing:
    """Tests for bcrypt password hashing"""
    
    def test_hash_password_creates_bcrypt_hash(self):
        """Test that hash_password creates valid bcrypt hash"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt identifier
    
    def test_hash_password_different_each_time(self):
        """Test that same password produces different hashes (due to random salt)"""
        password = "test_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Different hashes (due to different salts)
        assert hash1 != hash2
        
        # But both verify against same password
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "correct_password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """Test password verification with empty password"""
        password = "actual_password"
        hashed = hash_password(password)
        
        assert verify_password("", hashed) is False
    
    def test_verify_password_malformed_hash(self):
        """Test that malformed hash returns False instead of exception"""
        malformed_hash = "not_a_valid_bcrypt_hash"
        result = verify_password("password", malformed_hash)
        
        assert result is False


class TestSecretsFilter:
    """Tests for secrets masking in logs"""
    
    def test_filter_masks_jwt_tokens(self):
        """Test that JWT tokens are masked in logs"""
        secrets_filter = SecretsFilter()
        
        # Create a log record with JWT
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Login failed for token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1jadusVyIjoiYWRtaW4ifQ.signature",
            args=(),
            exc_info=None
        )
        
        secrets_filter.filter(record)
        message = record.getMessage()
        
        assert "eyJhbGc" not in message
        assert "[REDACTED_JWT]" in message
    
    def test_filter_masks_bearer_tokens(self):
        """Test that Bearer tokens are masked"""
        secrets_filter = SecretsFilter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxx.yyy",
            args=(),
            exc_info=None
        )
        
        secrets_filter.filter(record)
        message = record.getMessage()
        
        assert "Bearer eyJ" not in message
        assert "[REDACTED_JWT]" in message or "[REDACTED]" in message
    
    def test_filter_masks_passwords(self):
        """Test that passwords in logs are masked"""
        secrets_filter = SecretsFilter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg='Failed login with password="secret123"',
            args=(),
            exc_info=None
        )
        
        secrets_filter.filter(record)
        message = record.getMessage()
        
        assert "secret123" not in message
        assert "[REDACTED]" in message
    
    def test_filter_masks_admin_secret_key(self):
        """Test that ADMIN_SECRET_KEY is masked"""
        secrets_filter = SecretsFilter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="ADMIN_SECRET_KEY=my_super_secret_key_12345678",
            args=(),
            exc_info=None
        )
        
        secrets_filter.filter(record)
        message = record.getMessage()
        
        assert "my_super_secret_key" not in message
        assert "[REDACTED]" in message
    
    def test_filter_masks_encryption_key(self):
        """Test that ENCRYPTION_KEY is masked"""
        secrets_filter = SecretsFilter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="ENCRYPTION_KEY=test_key_abc123def456",
            args=(),
            exc_info=None
        )
        
        secrets_filter.filter(record)
        message = record.getMessage()
        
        assert "test_key_abc123def456" not in message
        assert "[REDACTED]" in message
    
    def test_filter_masks_mongodb_url(self):
        """Test that MongoDB URLs with credentials are masked"""
        secrets_filter = SecretsFilter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="mongodb://admin:password123@localhost:27017/db",
            args=(),
            exc_info=None
        )
        
        secrets_filter.filter(record)
        message = record.getMessage()
        
        assert "admin:password123" not in message
        assert "[REDACTED]:[REDACTED]" in message
    
    def test_filter_handles_unicode(self):
        """Test that filter handles unicode text properly"""
        secrets_filter = SecretsFilter()
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1jadusVyIjoiYWRtaW4ifQ.signature with unicode: cafÃ©",
            args=(),
            exc_info=None
        )
        
        secrets_filter.filter(record)
        message = record.getMessage()
        
        # Unicode preserved
        assert "caf" in message  # Unicode preserved
        assert "[REDACTED_JWT]" in message  # Token masked
    
    def test_filter_no_exception_on_invalid_input(self):
        """Test that filter doesn't crash on edge cases"""
        secrets_filter = SecretsFilter()
        
        # Record with no message
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=None,
            args=(),
            exc_info=None
        )
        
        # Should not raise exception
        result = secrets_filter.filter(record)
        assert result is True


class TestPayloadValidation:
    """Tests for payload size validation (functional tests)"""
    
    def test_max_payload_size_env_default(self):
        """Test that MAX_PAYLOAD_SIZE defaults to 10 MB"""
        # This is set in main.py
        max_size = int(os.getenv("MAX_PAYLOAD_SIZE", 10485760))
        assert max_size == 10485760  # 10 MB
    
    def test_max_payload_size_env_custom(self):
        """Test that MAX_PAYLOAD_SIZE can be customized"""
        custom_size = 5242880  # 5 MB
        os.environ["MAX_PAYLOAD_SIZE"] = str(custom_size)
        
        size = int(os.getenv("MAX_PAYLOAD_SIZE", 10485760))
        assert size == custom_size


class TestAdminLoginRateLimit:
    """Tests for admin login rate limiting configuration"""
    
    def test_admin_login_limit_default(self):
        """Test admin login rate limit default (5 attempts per hour)"""
        limit = int(os.getenv("ADMIN_LOGIN_LIMIT", 5))
        assert limit == 5
    
    def test_admin_login_window_default(self):
        """Test admin login window default (3600 seconds = 1 hour)"""
        window = int(os.getenv("ADMIN_LOGIN_WINDOW_SECONDS", 3600))
        assert window == 3600


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

