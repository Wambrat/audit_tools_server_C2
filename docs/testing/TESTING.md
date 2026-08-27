# ðŸ§ª Testing Guide - StratÃ©gie & ExÃ©cution

Documentation complète du testing du système Jadus Audit.

---

## ðŸ“Š RÃ©sumÃ©

| MÃ©trique | Valeur |
|----------|--------|
| **Tests Unitaires** | 376 âœ… |
| **Couverture Code** | >95% |
| **Tests de SÃ©curitÃ©** | 133 |
| **Temps Total** | ~21 secondes |
| **Status** | ALL PASSING âœ… |

---

## ðŸŽ¯ StratÃ©gie de Testing

### 4 Niveaux

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  LEVEL 1: Unit Tests (376 tests)                â”‚
â”‚  - Chaque fonction testÃ©e isolÃ©ment             â”‚
â”‚  - Mocks + Fixtures                             â”‚
â”‚  - Coverage >95%                                 â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                    â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  LEVEL 2: Security Tests (133 tests)            â”‚
â”‚  - SQL Injection: 59 tests                       â”‚
â”‚  - CORS: 45 tests                                â”‚
â”‚  - Session Management: 29 tests                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                    â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  LEVEL 3: Integration Tests                     â”‚
â”‚  - API endpoints end-to-end                     â”‚
â”‚  - Database interaction                         â”‚
â”‚  - Rate limiting                                 â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                    â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  LEVEL 4: E2E Tests (PowerShell scripts)        â”‚
â”‚  - Full workflow (enroll â†’ beacon â†’ results)    â”‚
â”‚  - Dashboard validation                         â”‚
â”‚  - Real agent execution                         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## ðŸš€ ExÃ©cuter les Tests

### Tous les Tests (ComplÃ¨te)

```bash
python -m pytest test/ -v
```

**RÃ©sultat:**
```
collected 376 items

test/test_sql_injection_prevention.py::test_union_based_injection PASSED
test/test_sql_injection_prevention.py::test_boolean_blind_injection PASSED
... (376 tests)

==================== 376 passed in 21.05s ====================
```

**Temps:** ~21 secondes

### Tests Rapides (Subset)

```bash
# Unit tests seulement (pas de sÃ©curitÃ©)
python -m pytest test/ -k "not sql and not cors and not session" -v

# Ou un module spÃ©cifique
python -m pytest test/test_models.py -v
```

### Tests de SÃ©curitÃ© SpÃ©cifiques

```bash
# SQL Injection
python -m pytest test/test_sql_injection_prevention.py -v

# CORS
python -m pytest test/test_cors_security.py -v

# Session Management
python -m pytest test/test_session_management.py -v
```

### Coverage

```bash
# GÃ©nÃ©rer rapport de couverture
python -m pytest test/ --cov=app --cov-report=html

# Ouvrir le rapport
open htmlcov/index.html  # macOS/Linux
start htmlcov\index.html # Windows
```

---

## ðŸ“ Structure des Tests

```
test/
â”œâ”€â”€ test_sql_injection_prevention.py      # 59 tests
â”œâ”€â”€ test_cors_security.py                 # 45 tests
â”œâ”€â”€ test_session_management.py            # 29 tests
â”œâ”€â”€ test_encryption.py                    # 29 tests
â”œâ”€â”€ test_admin_auth.py                    # 29 tests
â”œâ”€â”€ test_models.py                        # 40+ tests
â”œâ”€â”€ test_database.py                      # 30+ tests
â”œâ”€â”€ test_monitoring.py                    # 25+ tests
â”œâ”€â”€ test_routes.py                        # 30+ tests
â””â”€â”€ test_audit_logger.py                  # 20+ tests
```

---

## ðŸ” Tests de SÃ©curitÃ© DÃ©taillÃ©s

### 1ï¸âƒ£ SQL Injection Prevention (59 tests)

**Fichier:** `test/test_sql_injection_prevention.py`

**Vecteurs testÃ©s:**

```python
# UNION-based injection
âŒ "SELECT * FROM agents WHERE id = 1 UNION SELECT * FROM users"

# Boolean-based blind injection
âŒ "SELECT * FROM agents WHERE id = 1 AND 1=1"

# Time-based blind injection
âŒ "SELECT * FROM agents WHERE id = 1; WAITFOR DELAY '00:00:05'"

# Error-based injection
âŒ "SELECT * FROM agents WHERE id = EXTRACTVALUE(1, CONCAT(0x7e, ...))"

# Stacked queries
âŒ "SELECT * FROM agents; DROP TABLE users;--"

# Comment injection
âŒ "SELECT * FROM agents WHERE id = 1 -- comment"

# Wildcard injection
âŒ "SELECT * FROM agents WHERE name LIKE '%' OR '1'='1'%"
```

**Tests inclus:**

```
âœ… Pattern detection (20 tests)
âœ… Parameterized queries (15 tests)
âœ… Edge cases & encoding (24 tests)
```

**RÃ©sultat:**
```
test_sql_injection_prevention.py::test_union_based PASSED
test_sql_injection_prevention.py::test_boolean_blind PASSED
... (59 tests)
==================== 59 passed ====================
```

---

### 2ï¸âƒ£ CORS Security (45 tests)

**Fichier:** `test/test_cors_security.py`

**Tests:**

```python
# Origin validation
âœ… test_exact_origin_match
âœ… test_subdomain_wildcard
âœ… test_regex_pattern
âœ… test_reject_unauthorized_origin

# Method validation
âœ… test_allowed_methods
âœ… test_reject_unauthorized_methods

# Dangerous headers
âœ… test_filter_authorization_header
âœ… test_filter_cookie_header
âœ… test_filter_set_cookie_header

# Credentials
âœ… test_credentials_allowed
âœ… test_credentials_disabled_with_wildcard
```

**RÃ©sultat:**
```
test_cors_security.py PASSED [100%]
==================== 45 passed ====================
```

---

### 3ï¸âƒ£ Session Management & Key Rotation (29 tests)

**Fichier:** `test/test_session_management.py`

**Tests:**

```python
# Session creation & validation
âœ… test_create_session
âœ… test_validate_valid_session
âœ… test_reject_expired_session

# Session regeneration
âœ… test_regenerate_session
âœ… test_old_session_invalidated

# Key rotation
âœ… test_rotate_key
âœ… test_old_key_retained
âœ… test_max_active_keys_limit

# IP & User-Agent consistency
âœ… test_ip_change_detected
âœ… test_user_agent_change_detected
```

**RÃ©sultat:**
```
test_session_management.py PASSED [100%]
==================== 29 passed ====================
```

---

## ðŸš€ PowerShell Testing Scripts

Scripts automatisÃ©s pour tester l'API:

### `scripts/test/quick_api_test.ps1` - 5 Tests (30 sec)

```powershell
.\scripts\test\quick_api_test.ps1
```

**Tests:**
1. Health Check
2. Swagger UI
3. Agent Enrollment
4. Agent Beacon
5. Security Headers

**RÃ©sultat:**
```
1. Health Check... [OK] HTTP 200
2. Swagger UI... [OK] HTTP 200
3. Agent Enrollment... [OK]
4. Agent Beacon... [OK]
5. Security Headers... [OK] 4/4 headers found
```

---

### `scripts/test/debug_api_test.ps1` - Verbose (1 min)

```powershell
.\scripts\test\debug_api_test.ps1
```

**Affiche:**
- Status codes dÃ©taillÃ©s
- Response bodies (JSON)
- Headers
- Errors avec contexte

**Utile pour:**
- DÃ©boguer les erreurs API
- VÃ©rifier les headers exactes
- Valider la structure JSON

---

### `scripts/test/test_backend_complete.ps1` - Complet (5 min)

```powershell
.\scripts\test\test_backend_complete.ps1
```

**Tests:**
1. pytest (376 tests)
2. Server startup
3. API docs
4. Endpoints (enroll, beacon, results)
5. Rate limiting
6. Security
7. Integration
8. Logs

---

## ðŸ§ª Test-Driven Development (TDD)

### Workflow TDD utilisÃ©

```
1. Ã‰crire un test qui Ã©choue âŒ
   â†“
2. Ã‰crire le code minimum pour passer le test âœ…
   â†“
3. Refactoriser et amÃ©liorer le code ðŸ”„
   â†“
4. Tous les tests continuent de passer âœ…
```

### Exemple: SQL Injection Prevention

```python
# 1. Test (Ã©crit d'abord)
def test_union_injection_detected():
    pattern = detect_injection_pattern("SELECT * UNION SELECT * FROM users")
    assert pattern == SQLDangerPattern.UNION_BASED

# 2. Code minimum
def detect_injection_pattern(query: str):
    if "UNION SELECT" in query.upper():
        return SQLDangerPattern.UNION_BASED
    return None

# 3. Refactoriser
# (ImplÃ©menter tous les patterns, optimiser regex, etc.)

# 4. VÃ©rifier tous les tests passent
# pytest test/test_sql_injection_prevention.py -v
```

---

## ðŸ“ˆ Coverage

### Couverture par Module

| Module | Coverage | Tests |
|--------|----------|-------|
| `sql_injection_prevention.py` | 100% | 59 |
| `cors_security.py` | 100% | 45 |
| `session_management.py` | 100% | 29 |
| `encryption.py` | 100% | 29 |
| `admin_auth.py` | 100% | 29 |
| `models.py` | 95% | 40+ |
| `routes.py` | 95% | 30+ |
| **Total** | **>95%** | **376** |

### Voir le Rapport

```bash
# GÃ©nÃ©rer
python -m pytest test/ --cov=app --cov-report=html

# Ouvrir
open htmlcov/index.html
```

---

## ðŸ” Debugging Failed Tests

### Ã‰tape 1: Voir l'erreur complÃ¨te

```bash
python -m pytest test/test_sql_injection_prevention.py::test_union_based -v
```

### Ã‰tape 2: Mode verbose

```bash
python -m pytest test/ -vv --tb=long
```

### Ã‰tape 3: Stop au premier Ã©chec

```bash
python -m pytest test/ -x  # ArrÃªte au premier Ã©chec
```

### Ã‰tape 4: Lancer 1 test spÃ©cifique

```bash
python -m pytest test/test_models.py::test_agent_creation -v
```

---

## ðŸ› ProblÃ¨mes Courants

### "ModuleNotFoundError: No module named 'app'"

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # Linux/macOS
. venv\Scripts\Activate.ps1  # Windows
```

### "Cannot connect to database"

```bash
# Les tests utilisent une BD in-memory, vÃ©rifier la config .env
cat .env | grep DATABASE_MODE

# Doit Ãªtre: DATABASE_MODE=memory (pour les tests)
```

### Test timeout (30+ secondes)

```bash
# Utiliser pytest avec timeout
pip install pytest-timeout

python -m pytest test/ --timeout=10
```

---

## âœ… Checklist Pre-Commit

Avant de commiter:

- [ ] Tous les tests passent: `pytest test/ -q`
- [ ] Coverage >95%: `pytest test/ --cov=app`
- [ ] Pas de warnings: `pytest test/ -W error`
- [ ] Code formatÃ©: `black app/ test/`
- [ ] Linting OK: `pylint app/`

---

## ðŸ“š Ressources

- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://testpyramid.com/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

---

## ðŸš€ IntÃ©gration Continue (CI/CD)

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest test/ -v
      - run: pytest test/ --cov=app
```

---

**Last Updated:** 2026-06-16

ðŸ“– **Pour plus de dÃ©tails:** Voir [Testing Scripts Index](../../scripts/README.md)

