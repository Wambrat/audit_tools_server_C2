"""
Encryption Module - AES-256-GCM Encryption for Audit Results

This module provides encryption/decryption functionality for sensitive audit results.
Uses AES-256-GCM (Galois/Counter Mode) for authenticated encryption.
"""

import os
import base64
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import hashlib


class EncryptionError(Exception):
    """Raised when encryption/decryption fails"""
    pass


class Encryptor:
    """
    Handles AES-256-GCM encryption and decryption of audit results.
    
    Features:
    - AES-256-GCM authenticated encryption
    - PBKDF2 key derivation from master key
    - Base64 encoding for storage
    - Hash generation for searching/auditing
    - Random nonce per encryption (secures against replay attacks)
    """
    
    def __init__(self, master_key: str = None):
        """
        Initialize Encryptor with master key.
        
        Args:
            master_key: The encryption key (or read from ENCRYPTION_KEY env var)
                       Should be at least 32 chars for good security
        
        Raises:
            EncryptionError: If no key is provided or key is too short
        """
        self.master_key = master_key or os.getenv("ENCRYPTION_KEY")
        
        if not self.master_key:
            raise EncryptionError(
                "ENCRYPTION_KEY env var not set or master_key not provided. "
                "Set: export ENCRYPTION_KEY='your-secure-key-min-32-chars'"
            )
        
        if len(self.master_key) < 16:
            raise EncryptionError(
                f"Encryption key too short ({len(self.master_key)} chars). "
                "Minimum 32 characters recommended."
            )
    
    def _derive_key(self, salt: bytes) -> bytes:
        """
        Derive a 256-bit key from master key using PBKDF2.
        
        Args:
            salt: Random salt for key derivation
        
        Returns:
            32-byte encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP recommended
        )
        return kdf.derive(self.master_key.encode())
    
    def encrypt(self, plaintext: str) -> Tuple[str, str]:
        """
        Encrypt plaintext using AES-256-GCM.
        
        Args:
            plaintext: String to encrypt (e.g., audit result)
        
        Returns:
            Tuple of (encrypted_b64, nonce_b64) where:
            - encrypted_b64: Base64 encoded ciphertext+tag
            - nonce_b64: Base64 encoded nonce (random per encryption)
        
        Raises:
            EncryptionError: If encryption fails
        """
        try:
            # Generate random nonce (96-bit = 12 bytes is standard for GCM)
            nonce = os.urandom(12)
            
            # Generate random salt for key derivation
            salt = os.urandom(16)
            
            # Derive key from master key
            key = self._derive_key(salt)
            
            # Create cipher
            cipher = AESGCM(key)
            
            # Encrypt (returns ciphertext + authentication tag)
            ciphertext = cipher.encrypt(nonce, plaintext.encode(), None)
            
            # Encode to base64 for storage (binary → string)
            # Format: nonce + salt + ciphertext (all binary, then base64)
            encrypted_data = nonce + salt + ciphertext
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            return encrypted_b64, nonce.hex()
            
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_b64: str) -> str:
        """
        Decrypt AES-256-GCM encrypted data.
        
        Args:
            encrypted_b64: Base64 encoded encrypted data (nonce + salt + ciphertext)
        
        Returns:
            Decrypted plaintext
        
        Raises:
            EncryptionError: If decryption fails or authentication fails
        """
        try:
            # Decode base64
            encrypted_data = base64.b64decode(encrypted_b64)
            
            # Extract components
            nonce = encrypted_data[:12]           # First 12 bytes
            salt = encrypted_data[12:28]          # Next 16 bytes
            ciphertext = encrypted_data[28:]      # Rest is ciphertext+tag
            
            # Derive same key
            key = self._derive_key(salt)
            
            # Create cipher and decrypt
            cipher = AESGCM(key)
            plaintext = cipher.decrypt(nonce, ciphertext, None)
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            raise EncryptionError(
                f"Decryption failed (wrong key? corrupted data?): {str(e)}"
            )
    
    @staticmethod
    def hash_result(plaintext: str) -> str:
        """
        Generate SHA-256 hash of plaintext for searching/auditing.
        
        Allows searching for exact matches without decryption.
        Also useful for integrity checking.
        
        Args:
            plaintext: String to hash
        
        Returns:
            Hex string of SHA-256 hash
        """
        return hashlib.sha256(plaintext.encode()).hexdigest()
    
    @staticmethod
    def generate_preview(plaintext: str, max_length: int = 100) -> str:
        """
        Generate a non-sensitive preview of the result.
        
        Shows structure/size but not sensitive content.
        
        Args:
            plaintext: The audit result
            max_length: Max length of preview
        
        Returns:
            Safe preview string (e.g., "PowerShell output: 2500 bytes, 45 lines")
        """
        lines = plaintext.split('\n')
        bytes_count = len(plaintext.encode('utf-8'))
        
        # Generate safe summary
        if len(plaintext) > max_length:
            preview = plaintext[:max_length] + "..."
        else:
            preview = plaintext
        
        # Count info
        line_count = len([l for l in lines if l.strip()])
        
        return f"Output: {bytes_count} bytes, {line_count} lines"


# Singleton instance for the application
_encryptor = None


def get_encryptor(master_key: str = None) -> Encryptor:
    """
    Get or create the Encryptor singleton instance.
    
    Args:
        master_key: Optional master key to initialize
    
    Returns:
        Encryptor instance
    
    Raises:
        EncryptionError: If encryption is not properly configured
    """
    global _encryptor
    
    if _encryptor is None:
        _encryptor = Encryptor(master_key)
    
    return _encryptor


def set_encryptor(master_key: str) -> Encryptor:
    """
    Set or reset the Encryptor singleton instance.
    
    Useful for testing or changing keys at runtime.
    
    Args:
        master_key: Master key to use
    
    Returns:
        New Encryptor instance
    """
    global _encryptor
    _encryptor = Encryptor(master_key)
    return _encryptor
