"""
Unit Tests for Encryption Module - AES-256-GCM Encryption

Tests cover:
- Encryption/decryption round-trip
- Authentication (tampering detection)
- Hash generation and verification
- Preview generation
- Key derivation consistency
- Error handling
"""

import pytest
from app.encryption import (
    Encryptor, EncryptionError, get_encryptor, set_encryptor,
    _encryptor
)


class TestEncryptor:
    """Test cases for Encryptor class"""
    
    def test_encryptor_init_success(self):
        """Test Encryptor initialization with valid key"""
        key = "a" * 32  # 32-char key
        encryptor = Encryptor(key)
        assert encryptor.master_key == key
    
    def test_encryptor_init_no_key_no_env(self):
        """Test Encryptor raises error when no key provided and env var not set"""
        import os
        # Make sure env var is not set
        old_key = os.environ.get("ENCRYPTION_KEY")
        if "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]
        
        try:
            with pytest.raises(EncryptionError, match="ENCRYPTION_KEY env var not set"):
                Encryptor(None)
        finally:
            if old_key:
                os.environ["ENCRYPTION_KEY"] = old_key
    
    def test_encryptor_init_key_too_short(self):
        """Test Encryptor raises error when key is too short"""
        key = "short"  # Too short
        with pytest.raises(EncryptionError, match="too short"):
            Encryptor(key)
    
    def test_encrypt_returns_tuple(self):
        """Test encrypt returns tuple of (encrypted_b64, nonce_hex)"""
        encryptor = Encryptor("a" * 32)
        plaintext = "Hello, World!"
        
        encrypted_b64, nonce_hex = encryptor.encrypt(plaintext)
        
        assert isinstance(encrypted_b64, str)
        assert isinstance(nonce_hex, str)
        assert len(nonce_hex) == 24  # 12 bytes as hex = 24 chars
        assert encrypted_b64 != plaintext  # Should be encrypted
    
    def test_encrypt_empty_string(self):
        """Test encrypting empty string"""
        encryptor = Encryptor("a" * 32)
        plaintext = ""
        
        encrypted_b64, nonce_hex = encryptor.encrypt(plaintext)
        
        assert isinstance(encrypted_b64, str)
        assert len(encrypted_b64) > 0
    
    def test_encrypt_long_text(self):
        """Test encrypting large text (PowerShell output)"""
        encryptor = Encryptor("a" * 32)
        # Simulate large PowerShell output
        plaintext = "PowerShell Output:\n" + "\n".join([f"Line {i}: {i*100}" for i in range(100)])
        
        encrypted_b64, nonce_hex = encryptor.encrypt(plaintext)
        
        assert len(encrypted_b64) > len(plaintext) * 1.3  # Should be larger (base64 overhead)
    
    def test_encrypt_special_characters(self):
        """Test encrypting text with special characters"""
        encryptor = Encryptor("a" * 32)
        plaintext = "Special chars: !@#$%^&*()_+{}[]|\\:;\"'<>,.?/~`"
        
        encrypted_b64, nonce_hex = encryptor.encrypt(plaintext)
        
        assert encrypted_b64 != plaintext
    
    def test_decrypt_success(self):
        """Test decrypt recovers plaintext"""
        encryptor = Encryptor("a" * 32)
        plaintext = "Secret audit data: Get-Service | Get-Process"
        
        encrypted_b64, _ = encryptor.encrypt(plaintext)
        decrypted = encryptor.decrypt(encrypted_b64)
        
        assert decrypted == plaintext
    
    def test_decrypt_wrong_key(self):
        """Test decrypt fails with wrong key"""
        encryptor1 = Encryptor("a" * 32)
        encryptor2 = Encryptor("b" * 32)
        
        plaintext = "Sensitive data"
        encrypted_b64, _ = encryptor1.encrypt(plaintext)
        
        with pytest.raises(EncryptionError):
            encryptor2.decrypt(encrypted_b64)
    
    def test_decrypt_tampered_data(self):
        """Test decrypt fails when data is tampered"""
        encryptor = Encryptor("a" * 32)
        plaintext = "Original data"
        
        encrypted_b64, _ = encryptor.encrypt(plaintext)
        
        # Tamper with the data
        tampered_b64 = encrypted_b64[:-10] + "AAAAAAAAAA"
        
        with pytest.raises(EncryptionError):
            encryptor.decrypt(tampered_b64)
    
    def test_decrypt_corrupted_base64(self):
        """Test decrypt fails with invalid base64"""
        encryptor = Encryptor("a" * 32)
        
        with pytest.raises(EncryptionError):
            encryptor.decrypt("not-valid-base64-!!!")
    
    def test_encrypt_decrypt_round_trip(self):
        """Test multiple round-trip encryptions"""
        encryptor = Encryptor("a" * 32)
        
        plaintexts = [
            "Simple text",
            "Multi\nline\ntext",
            "Unicode: café, naïve, résumé",
            "JSON: {\"key\": \"value\"}",
            "",
        ]
        
        for plaintext in plaintexts:
            encrypted_b64, _ = encryptor.encrypt(plaintext)
            decrypted = encryptor.decrypt(encrypted_b64)
            assert decrypted == plaintext, f"Round-trip failed for: {plaintext}"
    
    def test_different_encryptions_different_ciphertext(self):
        """Test same plaintext encrypts differently each time (random nonce)"""
        encryptor = Encryptor("a" * 32)
        plaintext = "Same text"
        
        encrypted1, _ = encryptor.encrypt(plaintext)
        encrypted2, _ = encryptor.encrypt(plaintext)
        
        # Should be different due to random nonce
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same plaintext
        assert encryptor.decrypt(encrypted1) == plaintext
        assert encryptor.decrypt(encrypted2) == plaintext
    
    def test_hash_result_consistency(self):
        """Test hash_result produces consistent hash"""
        plaintext = "Audit result to hash"
        
        hash1 = Encryptor.hash_result(plaintext)
        hash2 = Encryptor.hash_result(plaintext)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 is 64 hex chars
    
    def test_hash_result_different_for_different_text(self):
        """Test different text produces different hash"""
        hash1 = Encryptor.hash_result("Text 1")
        hash2 = Encryptor.hash_result("Text 2")
        
        assert hash1 != hash2
    
    def test_hash_result_case_sensitive(self):
        """Test hash is case-sensitive"""
        hash1 = Encryptor.hash_result("Hello")
        hash2 = Encryptor.hash_result("hello")
        
        assert hash1 != hash2
    
    def test_generate_preview_short_text(self):
        """Test preview for short text"""
        plaintext = "Short output"
        preview = Encryptor.generate_preview(plaintext)
        
        # Preview should not contain the actual text (safe)
        assert "Short output" not in preview
        # But should have info about it
        assert "Output:" in preview
        assert "bytes" in preview
    
    def test_generate_preview_long_text(self):
        """Test preview for long text"""
        plaintext = "x" * 5000
        preview = Encryptor.generate_preview(plaintext)
        
        assert "5000 bytes" in preview
        assert len(preview) < 200  # Preview is short, safe
    
    def test_generate_preview_multiline(self):
        """Test preview counts lines correctly"""
        plaintext = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        preview = Encryptor.generate_preview(plaintext)
        
        assert "5 lines" in preview
    
    def test_derive_key_consistent(self):
        """Test key derivation is consistent with same salt"""
        encryptor = Encryptor("a" * 32)
        
        salt = b"consistent_salt_"
        key1 = encryptor._derive_key(salt)
        key2 = encryptor._derive_key(salt)
        
        assert key1 == key2
        assert len(key1) == 32  # 256-bit key
    
    def test_derive_key_different_for_different_salt(self):
        """Test different salt produces different key"""
        encryptor = Encryptor("a" * 32)
        
        key1 = encryptor._derive_key(b"salt1___________")
        key2 = encryptor._derive_key(b"salt2___________")
        
        assert key1 != key2


class TestGetEncryptor:
    """Test cases for singleton encryptor"""
    
    def test_get_encryptor_first_call_initializes(self):
        """Test get_encryptor initializes on first call"""
        # Reset global
        import app.encryption
        app.encryption._encryptor = None
        
        encryptor = get_encryptor("a" * 32)
        assert encryptor is not None
        assert isinstance(encryptor, Encryptor)
    
    def test_get_encryptor_returns_same_instance(self):
        """Test get_encryptor returns same singleton"""
        import app.encryption
        app.encryption._encryptor = None
        
        encryptor1 = get_encryptor("a" * 32)
        encryptor2 = get_encryptor("b" * 32)  # Key ignored on second call
        
        assert encryptor1 is encryptor2
    
    def test_set_encryptor_replaces_instance(self):
        """Test set_encryptor replaces the singleton"""
        import app.encryption
        app.encryption._encryptor = None
        
        encryptor1 = set_encryptor("a" * 32)
        encryptor2 = set_encryptor("b" * 32)
        
        assert encryptor1 is not encryptor2


class TestEncryptionIntegration:
    """Integration tests with realistic scenarios"""
    
    def test_powershell_output_encryption(self):
        """Test encrypting realistic PowerShell output"""
        encryptor = Encryptor("a" * 32)
        
        # Realistic PowerShell Get-Service output
        powershell_output = """Status   Name               DisplayName
------   ----               -----------
Running  AdobeARMservice    Adobe Acrobat Update Service
Running  AdobeFlashPlaye... Adobe Flash Player Update Service
Stopped  AJRouter           AllJoyn Router Service
Running  Appinfo            Application Information
Running  AppMgmt            Application Management
Running  AppXSvc            AppX Deployment Service
Stopped  BITS               Background Intelligent Transfer Service"""
        
        encrypted_b64, nonce = encryptor.encrypt(powershell_output)
        decrypted = encryptor.decrypt(encrypted_b64)
        
        assert decrypted == powershell_output
    
    def test_json_result_encryption(self):
        """Test encrypting JSON audit results"""
        encryptor = Encryptor("a" * 32)
        import json
        
        result = {
            "command": "Get-SMBShare",
            "shares": [
                {"Name": "C$", "Path": "C:\\"},
                {"Name": "IPC$", "Path": ""},
            ],
            "timestamp": "2026-06-16T14:35:00Z"
        }
        result_json = json.dumps(result)
        
        encrypted_b64, _ = encryptor.encrypt(result_json)
        decrypted = encryptor.decrypt(encrypted_b64)
        
        assert json.loads(decrypted) == result
    
    def test_error_message_encryption(self):
        """Test encrypting error messages"""
        encryptor = Encryptor("a" * 32)
        
        error_msg = "Access denied to registry key: HKLM\\System\\CurrentControlSet"
        
        encrypted_b64, _ = encryptor.encrypt(error_msg)
        decrypted = encryptor.decrypt(encrypted_b64)
        
        assert decrypted == error_msg
        
        # Verify hash can be used for searching
        hash_val = encryptor.hash_result(error_msg)
        assert hash_val == encryptor.hash_result(error_msg)


class TestEncryptionWithDatabase:
    """Tests for encryption integration with Database"""
    
    def test_store_and_retrieve_encrypted_result(self):
        """Test storing and retrieving encrypted result from database"""
        from app.database import Database
        from datetime import datetime
        
        # Setup
        db = Database()
        encryptor = set_encryptor("a" * 32)
        
        # Create test data
        agent_id = "agent-1"
        task_id = "task-1"
        plaintext_result = "Get-Service: Services running successfully"
        
        # Store (should be encrypted)
        stored = db.store_result(
            task_id=task_id,
            agent_id=agent_id,
            status="success",
            result=plaintext_result,
            execution_time_ms=1234
        )
        
        # Verify encryption in storage
        assert stored.result_encrypted != plaintext_result
        assert stored.result_hash is not None
        assert stored.result_preview is not None
        
        # Retrieve (should be decrypted)
        retrieved = db.get_result(stored.result_id)
        assert retrieved.result == plaintext_result
        
        # Verify hash for searching
        expected_hash = encryptor.hash_result(plaintext_result)
        assert retrieved.result_hash == expected_hash
    
    def test_get_results_by_agent_decrypts(self):
        """Test get_results_by_agent decrypts all results"""
        from app.database import Database
        
        db = Database()
        set_encryptor("a" * 32)
        
        agent_id = "agent-1"
        
        # Store multiple results
        for i in range(3):
            db.store_result(
                task_id=f"task-{i}",
                agent_id=agent_id,
                status="success",
                result=f"Result {i}: some data here",
                execution_time_ms=1000+i
            )
        
        # Retrieve all
        results = db.get_results_by_agent(agent_id)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert f"Result {i}" in result.result
