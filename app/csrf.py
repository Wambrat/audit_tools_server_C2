"""
CSRF Protection - Cross-Site Request Forgery prevention

Implements double-submit cookie pattern with CSRF tokens.
Each POST/PUT/DELETE request requires a valid CSRF token.

Flow:
1. User loads page → Server generates CSRF token
2. Token stored in memory (secure cookie)
3. Form submission includes token in X-CSRF-Token header
4. Server validates token matches session
5. Request processed if token is valid
"""

import hmac
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CSRFProtection:
    """
    CSRF token generation and validation.
    
    Uses HMAC-SHA256 to generate unforgeable tokens.
    Tokens are time-limited and tied to sessions.
    """
    
    def __init__(self, secret_key: Optional[str] = None, token_lifetime_hours: int = 24):
        """
        Initialize CSRF protection.
        
        Args:
            secret_key: Secret for HMAC (generates from environment if not provided)
            token_lifetime_hours: How long tokens are valid
        """
        if secret_key is None:
            secret_key = os.getenv("CSRF_SECRET_KEY", os.getenv("ADMIN_SECRET_KEY", ""))
            if not secret_key:
                raise ValueError("CSRF_SECRET_KEY or ADMIN_SECRET_KEY environment variable not set")
        
        self.secret_key = secret_key.encode('utf-8')
        self.token_lifetime_hours = token_lifetime_hours
        self.tokens = {}  # In-memory token store: {token: (session_id, created_at)}
    
    def generate_token(self, session_id: str) -> str:
        """
        Generate a new CSRF token for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            CSRF token (hex string)
        """
        # Generate random nonce
        nonce = secrets.token_hex(16)
        
        # Create token: HMAC(session_id + timestamp + nonce, secret_key)
        timestamp = datetime.utcnow().isoformat()
        message = f"{session_id}:{timestamp}:{nonce}".encode('utf-8')
        
        token = hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).hexdigest()
        
        # Store token with metadata
        self.tokens[token] = {
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "nonce": nonce
        }
        
        logger.debug(f"CSRF token generated for session {session_id}")
        return token
    
    def validate_token(self, token: str, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a CSRF token.
        
        Args:
            token: CSRF token to validate
            session_id: Session identifier
            
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if token is valid
            - (False, reason) if token is invalid or expired
        """
        if not token:
            return False, "CSRF token missing"
        
        if token not in self.tokens:
            logger.warning(f"CSRF token validation failed: token not found (session: {session_id})")
            return False, "CSRF token invalid or expired"
        
        token_data = self.tokens[token]
        
        # Check session match
        if token_data["session_id"] != session_id:
            logger.warning(f"CSRF token session mismatch: expected {session_id}, got {token_data['session_id']}")
            return False, "CSRF token session mismatch"
        
        # Check expiration
        created_at = token_data["created_at"]
        expires_at = created_at + timedelta(hours=self.token_lifetime_hours)
        
        if datetime.utcnow() > expires_at:
            # Clean up expired token
            del self.tokens[token]
            logger.info(f"CSRF token expired: {token[:8]}... (session: {session_id})")
            return False, "CSRF token expired"
        
        logger.debug(f"CSRF token validated successfully (session: {session_id})")
        return True, None
    
    def cleanup_expired_tokens(self) -> int:
        """
        Remove expired tokens from storage.
        
        Returns:
            Number of tokens removed
        """
        expired_tokens = []
        now = datetime.utcnow()
        
        for token, data in self.tokens.items():
            created_at = data["created_at"]
            expires_at = created_at + timedelta(hours=self.token_lifetime_hours)
            if now > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.tokens[token]
        
        if expired_tokens:
            logger.info(f"CSRF token cleanup: removed {len(expired_tokens)} expired tokens")
        
        return len(expired_tokens)


# Global CSRF protection instance
_csrf_protection_instance = None


def get_csrf_protection() -> CSRFProtection:
    """Get or create CSRF protection singleton"""
    global _csrf_protection_instance
    if _csrf_protection_instance is None:
        _csrf_protection_instance = CSRFProtection()
    return _csrf_protection_instance
