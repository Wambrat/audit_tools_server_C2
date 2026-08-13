"""
Admin JWT Authentication Module

Provides JWT token generation and validation for admin access to monitoring endpoints.
Uses HS256 (HMAC with SHA-256) symmetric signing.

Environment Variables:
  - ADMIN_SECRET_KEY: Secret key for signing tokens (minimum 32 chars)
  - ADMIN_USERNAME: Admin username (default: "admin")
  - ADMIN_PASSWORD: Admin password hash (bcrypt format)
  - JWT_EXPIRATION_HOURS: Token expiration time (default: 24 hours)

Example:
    from app.admin_auth import verify_jwt_token, create_jwt_token
    
    # Generate token
    token = create_jwt_token("admin")
    
    # Verify token
    payload = verify_jwt_token(token)
    print(payload["username"])  # "admin"
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("C2")

# Configuration from environment
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "your-admin-secret-key-change-in-production-min-32-chars!!!")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", None)  # bcrypt hash
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
JWT_ALGORITHM = "HS256"

# For development: store plaintext password (will be hashed on first use)
ADMIN_PASSWORD_PLAINTEXT = os.getenv("ADMIN_PASSWORD", "change_me")

class JWTError(Exception):
    """Base exception for JWT errors"""
    pass


class TokenExpiredError(JWTError):
    """Token has expired"""
    pass


class TokenInvalidError(JWTError):
    """Token is invalid or malformed"""
    pass


def validate_secret_key():
    """
    Validate that secret key is secure enough for production.
    
    Raises:
        ValueError: If key is too short or uses default value
    """
    if ADMIN_SECRET_KEY == "your-admin-secret-key-change-in-production-min-32-chars!!!":
        logger.warning(
            "⚠️  Using default ADMIN_SECRET_KEY! Set ADMIN_SECRET_KEY environment variable in production"
        )
    
    if len(ADMIN_SECRET_KEY) < 32:
        raise ValueError(
            f"ADMIN_SECRET_KEY must be at least 32 characters (current: {len(ADMIN_SECRET_KEY)})"
        )


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Bcrypt hash as string
    
    Example:
        >>> hash_val = hash_password("changeme")
        >>> hash_val.startswith("$2b$")
        True
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its bcrypt hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hash to compare against
    
    Returns:
        True if password matches hash, False otherwise
    
    Example:
        >>> hashed = hash_password("changeme")
        >>> verify_password("changeme", hashed)
        True
        >>> verify_password("wrongpass", hashed)
        False
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_jwt_token(username: str) -> str:
    """
    Generate a JWT token for admin access.
    
    Args:
        username: Admin username (typically "admin")
    
    Returns:
        JWT token as string (format: "eyJ...")
    
    Raises:
        JWTError: If token generation fails
    
    Example:
        >>> token = create_jwt_token("admin")
        >>> token.startswith("eyJ")
        True
    """
    try:
        validate_secret_key()
        
        # Calculate expiration time
        expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        
        # Payload
        payload = {
            "username": username,
            "iat": datetime.utcnow(),  # Issued at
            "exp": expiration,         # Expiration
            "type": "admin"            # Token type
        }
        
        # Sign and encode
        token = jwt.encode(payload, ADMIN_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        logger.info(f"JWT token generated for user '{username}' (expires in {JWT_EXPIRATION_HOURS}h)")
        
        return token
    
    except Exception as e:
        logger.error(f"Failed to generate JWT token: {e}")
        raise JWTError(f"Token generation failed: {str(e)}")


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
    
    Returns:
        Decoded payload dictionary with keys:
        - username: Admin username
        - iat: Issued at timestamp
        - exp: Expiration timestamp
        - type: Token type ("admin")
    
    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid or malformed
        JWTError: If verification fails
    
    Example:
        >>> token = create_jwt_token("admin")
        >>> payload = verify_jwt_token(token)
        >>> payload["username"]
        'admin'
    """
    try:
        validate_secret_key()
        
        # Decode and verify
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verify token type
        if payload.get("type") != "admin":
            raise TokenInvalidError("Token is not an admin token")
        
        logger.debug(f"JWT token verified for user '{payload['username']}'")
        
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning(f"JWT token has expired")
        raise TokenExpiredError("Token has expired")
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise TokenInvalidError(f"Invalid token: {str(e)}")
    
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise JWTError(f"Verification failed: {str(e)}")


def verify_admin_credentials(username: str, password: str) -> bool:
    """
    Verify admin username and password.
    
    Uses bcrypt hashing for secure password verification.
    
    Args:
        username: Claimed username
        password: Claimed password
    
    Returns:
        True if credentials are correct, False otherwise
    
    Note:
        In production, ADMIN_PASSWORD_HASH should be set (bcrypt hash).
        For development, falls back to plaintext ADMIN_PASSWORD comparison.
    
    Example:
        >>> verify_admin_credentials("admin", "changeme")
        True
        >>> verify_admin_credentials("admin", "wrongpassword")
        False
    """
    # Check username
    if username != ADMIN_USERNAME:
        logger.warning(f"Failed admin login attempt for user '{username}'")
        return False
    
    # Use bcrypt hash if available (production)
    if ADMIN_PASSWORD_HASH:
        is_valid = verify_password(password, ADMIN_PASSWORD_HASH)
    else:
        # Fallback to plaintext for development (when ADMIN_PASSWORD_HASH not set)
        is_valid = password == ADMIN_PASSWORD_PLAINTEXT
    
    if not is_valid:
        logger.warning(f"Failed admin login attempt for user '{username}'")
    else:
        logger.info(f"Successful admin login for user '{username}'")
    
    return is_valid


def extract_token_from_header(authorization_header: Optional[str]) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    
    Args:
        authorization_header: Value of Authorization header (e.g., "Bearer eyJ...")
    
    Returns:
        Token string if valid format, None otherwise
    
    Example:
        >>> extract_token_from_header("Bearer eyJhbGc...")
        'eyJhbGc...'
        >>> extract_token_from_header("Invalid format")
        None
    """
    if not authorization_header:
        return None
    
    parts = authorization_header.split(" ")
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.debug(f"Invalid Authorization header format")
        return None
    
    return parts[1]
