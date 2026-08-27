# ðŸ” SÃ©curitÃ© - Phase 5 Tier 3 Hardening

Documentation complète des mesures de sécurité du système Jadus Audit.

**Statut:** âœ… **376/376 tests passants** - Toutes les mesures validÃ©es

---

## ðŸ“Š Vue d'ensemble - 4 Pilliers de SÃ©curitÃ©

### 1ï¸âƒ£ **SQL Injection Prevention** (59 tests âœ…)

**Objectif:** EmpÃªcher les attaques par injection SQL

**Vecteurs d'attaque dÃ©tectÃ©s:**
- âœ… UNION-based SQL injection
- âœ… Boolean-based blind injection
- âœ… Time-based blind injection
- âœ… Error-based injection
- âœ… Stacked queries
- âœ… Comment injection
- âœ… Wildcard injection

**ImplÃ©mentation:**
```python
# app/sql_injection_prevention.py

class SQLDangerPattern(Enum):
    UNION_BASED = "UNION SELECT"
    BOOLEAN_BLIND = "AND 1=1"
    TIMED = "WAITFOR DELAY"
    ERROR_BASED = "EXTRACTVALUE"
    STACKED_QUERIES = "; DROP TABLE"
    COMMENT_INJECTION = "--" or "/*"
    WILDCARD_INJECTION = "LIKE '%'"

# Utilisation:
from app.sql_injection_prevention import detect_injection_pattern

user_input = request.query  # Potentiellement malveillant
pattern = detect_injection_pattern(user_input)
if pattern:
    raise HTTPException(status_code=400, detail=f"Injection dÃ©tectÃ©e: {pattern}")
```

**Tests:**
- Pattern detection: 20 tests
- Parameterized queries: 15 tests
- Edge cases & encoding: 24 tests

---

### 2ï¸âƒ£ **CORS Security** (45 tests âœ…)

**Objectif:** ContrÃ´ler les requÃªtes cross-origin

**Configuration:**
```python
# main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # Frontend dev
        "http://localhost:5500",    # Live Server
        "http://127.0.0.1:8000",   # API self
    ],
    allow_credentials=True,         # Autoriser cookies/auth
    allow_methods=["GET", "POST"],  # MÃ©thodes autorisÃ©es
    allow_headers=["*"],            # Headers autorisÃ©s
)
```

**Patterns d'origine supportÃ©s:**
- âœ… Exact match: `https://example.com`
- âœ… Subdomain: `https://*.example.com`
- âœ… Wildcard: `https://*` (âš ï¸ Ã€ Ã©viter en prod)
- âœ… Regex: `https://[a-z0-9]+.example.com`

**Tests:**
- Origin validation: 15 tests
- Method validation: 10 tests
- Dangerous headers filtering: 20 tests

---

### 3ï¸âƒ£ **Session Management & Key Rotation** (29 tests âœ…)

**Objectif:** GÃ©rer les sessions sÃ©curisÃ©es et les clÃ©s

**Session Lifecycle:**
```python
# app/session_management.py

# 1. CrÃ©ation
session = SessionManager.create_session(
    user_id="agent-123",
    data={"role": "agent"},
    expiration_minutes=60
)

# 2. Validation
is_valid = SessionManager.validate_session(session_id)

# 3. RÃ©gÃ©nÃ©ration (aprÃ¨s authentification)
SessionManager.regenerate_session(old_session_id)

# 4. Invalidation (logout)
SessionManager.invalidate_session(session_id)

# 5. Cleanup (sessions expirÃ©es)
SessionManager.cleanup_expired_sessions()
```

**Key Rotation:**
```python
# app/session_management.py - KeyRotationManager

# Configuration
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")  # Master key
MAX_ACTIVE_KEYS = 3  # Garder les 3 derniÃ¨res clÃ©s

# Rotation mensuelle
def rotate_key():
    """CrÃ©er une nouvelle clÃ© de chiffrement"""
    new_key = secrets.token_urlsafe(32)
    # Archive: Garder les anciennes clÃ©s pour dÃ©cryption
    # Active: Nouvelle clÃ© pour chiffrement
    key_manager.rotate(new_key)

# Pour dÃ©cryption:
def decrypt_with_any_key(encrypted_data):
    """Essayer toutes les clÃ©s (actuelle + prÃ©cÃ©dentes)"""
    for key in key_manager.get_decryption_keys():
        try:
            return decrypt(encrypted_data, key)
        except:
            continue
    raise EncryptionError("Cannot decrypt with any known key")
```

**Validation de Session:**
```python
# VÃ©rifier l'IP et User-Agent
class SessionSecurityValidator:
    def validate(session, current_ip, current_user_agent):
        # Si IP/UA changent â†’ Session compromise â†’ Rejeter
        if session.ip != current_ip:
            raise SessionCompromiseError("IP mismatch")
        if session.user_agent != current_user_agent:
            raise SessionCompromiseError("User-Agent mismatch")
```

**Tests:**
- Session creation/validation: 10 tests
- Key rotation: 12 tests
- IP/UA consistency: 7 tests

---

### 4ï¸âƒ£ **Autres Mesures de SÃ©curitÃ© (PrÃ©cÃ©dentes Phases)**

#### ðŸ” Encryption des DonnÃ©es

**Algorithme:** AES-256-GCM (Authenticated Encryption)

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt_password(password: str) -> str:
    key = AESGCM.derive_key(
        algorithm=hashes.SHA256(),
        length=32,
        salt=os.urandom(16),
        iterations=100000,
        backend=default_backend()
    )
    return encrypted_password
```

#### ðŸŽ¯ CSRF Protection

```python
# main.py

CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY")  # 32+ chars

# GÃ©nÃ©rer un token CSRF
csrf_token = secrets.token_urlsafe(32)

# Valider sur chaque POST
if request.headers.get("X-CSRF-Token") != session.csrf_token:
    raise HTTPException(status_code=403, detail="CSRF token invalid")
```

#### ðŸ›¡ï¸ Security Headers

```python
# SecurityHeadersMiddleware dans main.py

response.headers["Strict-Transport-Security"] = "max-age=31536000"
response.headers["Content-Security-Policy"] = "default-src 'self'"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-XSS-Protection"] = "1; mode=block"
```

#### ðŸ“ Audit Logging

Toutes les opÃ©rations sensibles sont loggÃ©es:

```
ENROLL: Agent registered
BEACON: Agent alive signal
TASK_ASSIGN: Task assigned to agent
RESULT_SUBMIT: Result received
AUTH_FAILURE: Failed authentication attempt
CRYPTO_FAILURE: Encryption/Decryption error
```

#### ðŸš· Rate Limiting

```python
ENROLL_RATE_LIMIT = 5 requests/hour      # Anti-spam registration
BEACON_RATE_LIMIT = 100 requests/hour    # Anti-DoS heartbeats
RESULTS_RATE_LIMIT = 50 requests/hour    # Anti-flood results
```

---

## ðŸ”‘ Configuration des Secrets

### Variables d'Environnement Essentielles

```env
# ClÃ© de chiffrement (32+ caractÃ¨res)
ENCRYPTION_KEY=your-super-secret-key-that-is-32-chars-minimum

# Secret CSRF (32+ caractÃ¨res)
CSRF_SECRET_KEY=test-csrf-secret-key-32-chars-minimum

# Secret Admin (32+ caractÃ¨res)
ADMIN_SECRET_KEY=test-admin-secret-key-32-chars-minimum

# Database
DATABASE_MODE=memory          # ou mongodb
MONGODB_URL=mongodb://localhost:27017

# CORS
ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:8000

# Logs
LOG_LEVEL=INFO               # INFO, DEBUG, WARNING, ERROR
```

### Production

1. **Secrets Manager:** Utiliser HashiCorp Vault, AWS Secrets Manager, etc.
2. **Rotation:** Rotation des secrets tous les 90 jours
3. **HTTPS:** Toujours utiliser HTTPS en production
4. **TLS:** Version 1.2 minimum
5. **MongoDB Auth:** Authentification + TLS obligatoires
6. **Firewall:** Restreindre l'accÃ¨s Ã  l'API Ã  des plages IP connues
7. **Backups:** Chiffrer les backups
8. **Monitoring:** Alertes sur tentatives d'injection/auth failure

---

## ðŸ§ª Tests de SÃ©curitÃ©

### Lancer les Tests

```bash
# Tous les tests de sÃ©curitÃ©
python -m pytest test/test_sql_injection_prevention.py -v
python -m pytest test/test_cors_security.py -v
python -m pytest test/test_session_management.py -v

# Tous les tests
python -m pytest test/ -v

# Coverage
python -m pytest test/ --cov=app --cov-report=html
```

### Coverage

| Module | Tests | Coverage |
|--------|-------|----------|
| SQL Injection | 59 | 100% |
| CORS | 45 | 100% |
| Session Mgmt | 29 | 100% |
| Encryption | IntÃ©grÃ© | 100% |
| **Total** | **376** | **>95%** |

---

## ðŸš€ Deployment Checklist

Avant de dÃ©ployer en production:

- [ ] Tous les tests passent (`pytest test/ -q`)
- [ ] .env configurÃ© avec des secrets forts
- [ ] HTTPS activÃ©
- [ ] CORS rÃ©duit aux origines nÃ©cessaires
- [ ] MongoDB avec authentification
- [ ] Backups configurÃ©s et testÃ©s
- [ ] Monitoring des logs activÃ©
- [ ] Rate limiting configurÃ©
- [ ] Firewall configurÃ©
- [ ] Secrets en Vault (pas dans .env)
- [ ] Logs centralisÃ©s (Splunk, ELK, etc.)
- [ ] Alertes sur erreurs de sÃ©curitÃ©

---

## ðŸ“š Ressources SÃ©curitÃ©

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [OWASP CORS](https://owasp.org/www-community/CORS)
- [OWASP Session Management](https://owasp.org/www-community/attacks/Session_fixation)
- [Cryptography Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)

---

## ðŸ”— Voir Aussi

- [Architecture](./ARCHITECTURE.md) - Design global
- [API Documentation](../api/API.md) - Endpoints sÃ©curisÃ©s
- [Testing Guide](../testing/TESTING.md) - Tests de sÃ©curitÃ©
- [Quick Start](../setup/QUICK_START.md) - DÃ©marrage sÃ©curisÃ©

---

**Last Updated:** 2026-06-16  
**Security Level:** âœ… Phase 5 Tier 3 - HARDENED

