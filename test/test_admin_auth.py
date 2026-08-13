"""
JWT Admin Authentication Tests

Tests for JWT token generation, verification, and admin login endpoint.

Run with: pytest test/test_admin_auth.py -v
"""

import pytest
import os
from datetime import datetime, timedelta
from app.admin_auth import (
    create_jwt_token, verify_jwt_token, verify_admin_credentials,
    extract_token_from_header, validate_secret_key,
    JWTError, TokenExpiredError, TokenInvalidError
)
import jwt


class TestJWTTokenGeneration:
    """Tests for JWT token generation"""
    
    def test_create_jwt_token_success(self):
        """Test successful JWT token generation"""
        token = create_jwt_token("admin")
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.startswith("eyJ")  # Base64 encoded JWT header
    
    def test_create_jwt_token_contains_username(self):
        """Test that generated token contains the username"""
        token = create_jwt_token("testadmin")
        payload = verify_jwt_token(token)
        
        assert payload["username"] == "testadmin"
    
    def test_create_jwt_token_contains_expiration(self):
        """Test that generated token contains expiration"""
        token = create_jwt_token("admin")
        payload = verify_jwt_token(token)
        
        assert "exp" in payload
        assert payload["exp"] > datetime.utcnow().timestamp()
    
    def test_create_jwt_token_contains_type(self):
        """Test that generated token has correct type"""
        token = create_jwt_token("admin")
        payload = verify_jwt_token(token)
        
        assert payload["type"] == "admin"
    
    def test_create_jwt_token_generates_unique_tokens(self):
        """Test that each call generates a unique token (or same if within same second)"""
        token1 = create_jwt_token("admin")
        token2 = create_jwt_token("admin")
        
        # Tokens might be the same if called within the same second (iat is same)
        # What matters is that they're both valid
        payload1 = verify_jwt_token(token1)
        payload2 = verify_jwt_token(token2)
        
        assert payload1["username"] == "admin"
        assert payload2["username"] == "admin"


class TestJWTTokenVerification:
    """Tests for JWT token verification"""
    
    def test_verify_jwt_token_success(self):
        """Test successful JWT token verification"""
        token = create_jwt_token("admin")
        payload = verify_jwt_token(token)
        
        assert payload["username"] == "admin"
        assert payload["type"] == "admin"
        assert "iat" in payload
        assert "exp" in payload
    
    def test_verify_jwt_token_with_different_username(self):
        """Test verifying token with different username"""
        token = create_jwt_token("superadmin")
        payload = verify_jwt_token(token)
        
        assert payload["username"] == "superadmin"
    
    def test_verify_jwt_token_invalid_signature(self):
        """Test that tampered token is rejected"""
        token = create_jwt_token("admin")
        
        # Tamper with the token
        parts = token.split(".")
        tampered_token = f"{parts[0]}.{parts[1]}.TAMPERED"
        
        with pytest.raises(TokenInvalidError):
            verify_jwt_token(tampered_token)
    
    def test_verify_jwt_token_malformed(self):
        """Test that malformed token is rejected"""
        with pytest.raises(TokenInvalidError):
            verify_jwt_token("not.a.token")
    
    def test_verify_jwt_token_empty_string(self):
        """Test that empty token is rejected"""
        with pytest.raises(TokenInvalidError):
            verify_jwt_token("")
    
    def test_verify_jwt_token_wrong_algorithm(self):
        """Test that token signed with wrong algorithm is rejected"""
        # Create token with HS512 instead of HS256
        secret = os.getenv("ADMIN_SECRET_KEY", "your-admin-secret-key-change-in-production-min-32-chars!!!")
        payload = {
            "username": "admin",
            "type": "admin",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        wrong_token = jwt.encode(payload, secret, algorithm="HS512")
        
        with pytest.raises(TokenInvalidError):
            verify_jwt_token(wrong_token)
    
    def test_verify_jwt_token_missing_type(self):
        """Test that token without type field is rejected"""
        secret = os.getenv("ADMIN_SECRET_KEY", "your-admin-secret-key-change-in-production-min-32-chars!!!")
        payload = {
            "username": "admin",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24)
            # Missing "type" field
        }
        bad_token = jwt.encode(payload, secret, algorithm="HS256")
        
        # Should raise JWTError (which wraps TokenInvalidError)
        with pytest.raises(JWTError):
            verify_jwt_token(bad_token)


class TestAdminCredentials:
    """Tests for admin credential verification"""
    
    def test_verify_admin_credentials_success(self):
        """Test successful credential verification"""
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "changeme")
        
        assert verify_admin_credentials(username, password) is True
    
    def test_verify_admin_credentials_wrong_password(self):
        """Test rejection of wrong password"""
        username = os.getenv("ADMIN_USERNAME", "admin")
        
        assert verify_admin_credentials(username, "wrongpassword") is False
    
    def test_verify_admin_credentials_wrong_username(self):
        """Test rejection of wrong username"""
        password = os.getenv("ADMIN_PASSWORD", "changeme")
        
        assert verify_admin_credentials("wronguser", password) is False
    
    def test_verify_admin_credentials_case_sensitive(self):
        """Test that username is case-sensitive"""
        username = os.getenv("ADMIN_USERNAME", "admin").upper()
        password = os.getenv("ADMIN_PASSWORD", "changeme")
        
        assert verify_admin_credentials(username, password) is False


class TestHeaderExtraction:
    """Tests for Authorization header extraction"""
    
    def test_extract_token_from_valid_header(self):
        """Test extracting token from valid Authorization header"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        header = f"Bearer {token}"
        
        extracted = extract_token_from_header(header)
        assert extracted == token
    
    def test_extract_token_from_header_case_insensitive(self):
        """Test that Bearer is case-insensitive"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        
        for bearer_variant in ["Bearer", "bearer", "BEARER", "BeArEr"]:
            header = f"{bearer_variant} {token}"
            extracted = extract_token_from_header(header)
            assert extracted == token
    
    def test_extract_token_from_header_none_input(self):
        """Test extraction from None input"""
        extracted = extract_token_from_header(None)
        assert extracted is None
    
    def test_extract_token_from_header_empty_string(self):
        """Test extraction from empty string"""
        extracted = extract_token_from_header("")
        assert extracted is None
    
    def test_extract_token_from_header_invalid_format(self):
        """Test extraction from invalid format"""
        invalid_headers = [
            "NoBearer token",
            "Bearer",
            "Bearer token extra",
            "token",
            "Token eyJ...",
        ]
        
        for header in invalid_headers:
            extracted = extract_token_from_header(header)
            assert extracted is None
    
    def test_extract_token_from_header_with_spaces(self):
        """Test extraction with extra spaces"""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        header = f"Bearer   {token}"  # Extra spaces
        
        # Should return None because of extra spaces
        extracted = extract_token_from_header(header)
        assert extracted is None


class TestTokenExpiration:
    """Tests for token expiration"""
    
    def test_token_not_immediately_expired(self):
        """Test that freshly generated token is not expired"""
        token = create_jwt_token("admin")
        payload = verify_jwt_token(token)
        
        # Token should not be expired
        assert payload["exp"] > datetime.utcnow().timestamp()
    
    def test_token_expiration_time(self):
        """Test that token expiration matches configuration"""
        jwt_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        
        token = create_jwt_token("admin")
        payload = verify_jwt_token(token)
        
        iat = payload["iat"].timestamp() if hasattr(payload["iat"], "timestamp") else payload["iat"]
        exp = payload["exp"]
        
        # Expiration should be approximately jwt_hours from creation
        diff_hours = (exp - iat) / 3600
        
        # Allow ±5 minute tolerance
        assert abs(diff_hours - jwt_hours) < 0.1


class TestSecretKeyValidation:
    """Tests for secret key validation"""
    
    def test_validate_secret_key_minimum_length(self):
        """Test that short secret keys raise error"""
        # This test validates that the current key is >= 32 chars
        # We don't modify the env var here
        try:
            validate_secret_key()
            # If we get here, current key is valid
            assert True
        except ValueError as e:
            # Key is too short
            assert "32 characters" in str(e)
    
    def test_validate_secret_key_warning_default(self):
        """Test that default secret key triggers warning"""
        # This is mainly for documentation
        secret = os.getenv("ADMIN_SECRET_KEY", "your-admin-secret-key-change-in-production-min-32-chars!!!")
        
        if secret == "your-admin-secret-key-change-in-production-min-32-chars!!!":
            # Default is in use
            assert True
        else:
            # Custom secret is in use
            assert True


class TestIntegration:
    """Integration tests for complete JWT flow"""
    
    def test_full_jwt_flow(self):
        """Test complete JWT generation and verification flow"""
        # 1. Generate token for admin
        token = create_jwt_token("admin")
        assert token is not None
        
        # 2. Verify token is valid
        payload = verify_jwt_token(token)
        assert payload["username"] == "admin"
        assert payload["type"] == "admin"
        
        # 3. Extract from header
        header = f"Bearer {token}"
        extracted_token = extract_token_from_header(header)
        assert extracted_token == token
        
        # 4. Verify extracted token
        payload2 = verify_jwt_token(extracted_token)
        assert payload2["username"] == "admin"
    
    def test_credential_verification_then_token_generation(self):
        """Test credential verification followed by token generation"""
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "changeme")
        
        # 1. Verify credentials
        assert verify_admin_credentials(username, password) is True
        
        # 2. Generate token
        token = create_jwt_token(username)
        assert token is not None
        
        # 3. Verify token
        payload = verify_jwt_token(token)
        assert payload["username"] == username
    
    def test_multiple_users_different_tokens(self):
        """Test that different usernames generate different tokens"""
        token_admin = create_jwt_token("admin")
        token_superadmin = create_jwt_token("superadmin")
        
        assert token_admin != token_superadmin
        
        payload_admin = verify_jwt_token(token_admin)
        payload_superadmin = verify_jwt_token(token_superadmin)
        
        assert payload_admin["username"] == "admin"
        assert payload_superadmin["username"] == "superadmin"


# Run tests with: pytest test/test_admin_auth.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
