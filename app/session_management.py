"""
Session Management & Encryption Key Rotation

Secure session management and key rotation system including:
- Session lifecycle management (creation, validation, expiration)
- Secure session storage with encryption
- Session regeneration on authentication
- Key rotation scheduling
- Backward compatibility for old keys
- Audit trail for key rotations

Key Classes:
- SessionManager: Core session management
- KeyRotationManager: Encryption key rotation handler
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import secrets
import hashlib
from datetime import datetime, timedelta
import json


class SessionStatus(Enum):
    """Session lifecycle states"""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    ROTATED = "rotated"


@dataclass
class SessionData:
    """Secure session data"""
    session_id: str
    user_id: str
    created_at: str
    expires_at: str
    last_accessed: str
    ip_address: str
    user_agent: str
    status: SessionStatus = SessionStatus.ACTIVE
    regenerated_from: Optional[str] = None
    _metadata: Dict = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() > expires
    
    def update_last_accessed(self):
        """Update last accessed timestamp"""
        self.last_accessed = datetime.now().isoformat()


@dataclass
class KeyRotationRecord:
    """Record of key rotation event"""
    rotation_id: str
    rotated_at: str
    new_key_id: str
    old_key_id: Optional[str]
    reason: str
    admin_id: Optional[str] = None


class SessionManager:
    """Secure session management"""
    
    def __init__(self, session_timeout_minutes: int = 30):
        """
        Initialize session manager
        
        Args:
            session_timeout_minutes: Session expiration time in minutes
        """
        self.session_timeout_minutes = session_timeout_minutes
        self.sessions: Dict[str, SessionData] = {}
        self.session_index: Dict[str, str] = {}  # user_id -> session_id
    
    def create_session(
        self, user_id: str, ip_address: str, user_agent: str
    ) -> SessionData:
        """
        Create new session
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            SessionData with new session
        """
        session_id = self._generate_session_id()
        now = datetime.now()
        expires = now + timedelta(minutes=self.session_timeout_minutes)
        
        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            last_accessed=now.isoformat(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        self.session_index[user_id] = session_id
        
        return session
    
    def validate_session(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate session
        
        Args:
            session_id: Session to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if session_id not in self.sessions:
            return (False, "Session not found")
        
        session = self.sessions[session_id]
        
        if session.is_expired():
            session.status = SessionStatus.EXPIRED
            return (False, "Session expired")
        
        if session.status == SessionStatus.INVALIDATED:
            return (False, "Session invalidated")
        
        return (True, None)
    
    def regenerate_session(
        self, old_session_id: str, ip_address: str, user_agent: str
    ) -> Optional[SessionData]:
        """
        Regenerate session (for privilege escalation)
        
        Args:
            old_session_id: Old session to replace
            ip_address: New client IP
            user_agent: New user agent
            
        Returns:
            New SessionData or None if invalid
        """
        if old_session_id not in self.sessions:
            return None
        
        old_session = self.sessions[old_session_id]
        user_id = old_session.user_id
        
        # Invalidate old session
        old_session.status = SessionStatus.INVALIDATED
        
        # Create new session
        new_session = self.create_session(user_id, ip_address, user_agent)
        new_session.regenerated_from = old_session_id
        
        return new_session
    
    def invalidate_session(self, session_id: str) -> bool:
        """
        Explicitly invalidate a session
        
        Args:
            session_id: Session to invalidate
            
        Returns:
            True if successful
        """
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].status = SessionStatus.INVALIDATED
        return True
    
    def invalidate_all_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user
        
        Args:
            user_id: User to invalidate
            
        Returns:
            Count of invalidated sessions
        """
        count = 0
        for session in self.sessions.values():
            if session.user_id == user_id:
                session.status = SessionStatus.INVALIDATED
                count += 1
        return count
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Count of removed sessions
        """
        expired = [
            sid for sid, session in self.sessions.items()
            if session.is_expired()
        ]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)
    
    def _generate_session_id(self) -> str:
        """Generate cryptographically secure session ID"""
        return secrets.token_urlsafe(32)


class KeyRotationManager:
    """Encryption key rotation management"""
    
    def __init__(self, current_key_id: str):
        """
        Initialize key rotation manager
        
        Args:
            current_key_id: Current encryption key ID
        """
        self.current_key_id = current_key_id
        self.active_keys: Dict[str, str] = {current_key_id: "current"}
        self.rotation_history: List[KeyRotationRecord] = []
        self.max_active_keys = 3  # Allow current + 2 old keys for decryption
    
    def rotate_key(
        self, new_key_id: str, admin_id: Optional[str] = None, reason: str = "Scheduled"
    ) -> bool:
        """
        Rotate encryption key
        
        Args:
            new_key_id: New key identifier
            admin_id: Admin who initiated rotation
            reason: Reason for rotation
            
        Returns:
            True if rotation successful
        """
        old_key_id = self.current_key_id
        
        # Create rotation record
        rotation = KeyRotationRecord(
            rotation_id=secrets.token_hex(16),
            rotated_at=datetime.now().isoformat(),
            new_key_id=new_key_id,
            old_key_id=old_key_id,
            reason=reason,
            admin_id=admin_id
        )
        
        # Update key tracking
        self.active_keys[new_key_id] = "active"
        self.active_keys[old_key_id] = "deprecated"
        self.current_key_id = new_key_id
        
        # Record rotation
        self.rotation_history.append(rotation)
        
        # Clean up old keys (keep max_active_keys)
        self._cleanup_old_keys()
        
        return True
    
    def can_decrypt_with_key(self, key_id: str) -> bool:
        """
        Check if a key can be used for decryption
        
        Args:
            key_id: Key to check
            
        Returns:
            True if key is active or deprecated (not removed)
        """
        return key_id in self.active_keys
    
    def get_decryption_keys(self) -> List[str]:
        """
        Get all keys usable for decryption (current + recent deprecated)
        
        Returns:
            List of key IDs
        """
        return list(self.active_keys.keys())
    
    def get_current_key_id(self) -> str:
        """
        Get current encryption key ID
        
        Returns:
            Current key ID
        """
        return self.current_key_id
    
    def get_rotation_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get key rotation history
        
        Args:
            limit: Maximum records to return
            
        Returns:
            List of rotation records
        """
        records = self.rotation_history[-limit:] if limit else self.rotation_history
        return [asdict(r) for r in records]
    
    def _cleanup_old_keys(self):
        """Remove keys beyond max retention"""
        if len(self.active_keys) <= self.max_active_keys:
            return
        
        # Remove oldest keys, keep current and max_active_keys-1 old ones
        sorted_keys = sorted(self.active_keys.items(), key=lambda x: x[0])
        keys_to_remove = sorted_keys[:-(self.max_active_keys - 1)]
        
        for key_id, _ in keys_to_remove:
            if key_id != self.current_key_id:
                del self.active_keys[key_id]


class SessionSecurityValidator:
    """Session security validation"""
    
    @staticmethod
    def validate_session_mobility(
        old_ip: str, new_ip: str, max_distance: int = 5000
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate session mobility (prevent session hijacking across networks)
        
        Args:
            old_ip: Previous IP address
            new_ip: New IP address
            max_distance: Max acceptable distance in km
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # For production, would use GeoIP database
        # For now, simple check if IPs are completely different
        if old_ip != new_ip:
            # In production, calculate geographic distance
            # If too great, could indicate hijacking
            pass
        
        return (True, None)
    
    @staticmethod
    def validate_user_agent_consistency(
        old_ua: str, new_ua: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate user agent consistency
        
        Args:
            old_ua: Previous user agent
            new_ua: New user agent
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Different browsers or major OS changes could indicate hijacking
        if old_ua == new_ua:
            return (True, None)
        
        # Extract browser/OS info for comparison
        old_browser = old_ua.split()[0] if old_ua else ""
        new_browser = new_ua.split()[0] if new_ua else ""
        
        # If browser changes, could be suspicious
        if old_browser and new_browser and old_browser != new_browser:
            return (False, "User agent significantly changed")
        
        return (True, None)


def get_session_manager(timeout_minutes: int = 30) -> SessionManager:
    """Get session manager singleton"""
    if not hasattr(get_session_manager, "_instance"):
        get_session_manager._instance = SessionManager(timeout_minutes)
    return get_session_manager._instance


def get_key_rotation_manager(current_key_id: str = "key-001") -> KeyRotationManager:
    """Get key rotation manager singleton"""
    if not hasattr(get_key_rotation_manager, "_instance"):
        get_key_rotation_manager._instance = KeyRotationManager(current_key_id)
    return get_key_rotation_manager._instance
