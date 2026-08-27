# 🧪 Testing Guide - Stratégie & Exécution

Documentation complète du testing du système Jadus Audit.

---

## 📊 Résumé

| Métrique | Valeur |
|----------|--------|
| **Tests Unitaires** | 376 ✅ |
| **Couverture Code** | >95% |
| **Tests de Sécurité** | 133 |
| **Temps Total** | ~21 secondes |
| **Status** | ALL PASSING ✅ |

---

## 🎯 Stratégie de Testing

### 4 Niveaux

```
┌─────────────────────────────────────────────────┐
│  LEVEL 1: Unit Tests (376 tests)                │
│  - Chaque fonction testée isolément             │
│  - Mocks + Fixtures                             │
│  - Coverage >95%                                 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  LEVEL 2: Security Tests (133 tests)            │
│  - SQL Injection: 59 tests                       │
│  - CORS: 45 tests                                │
│  - Session Management: 29 tests                  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  LEVEL 3: Integration Tests                     │
│  - API endpoints end-to-end                     │
│  - Database interaction                         │
│  - Rate limiting                                 │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  LEVEL 4: E2E Tests (PowerShell scripts)        │
│  - Full workflow (enroll → beacon → results)    │
│  - Dashboard validation                         │
│  - Real agent execution                         │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Exécuter les Tests

### Tous les Tests (Complète)

```bash
python -m pytest test/ -v
```

**Résultat:**
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
# Unit tests seulement (pas de sécurité)
python -m pytest test/ -k "not sql and not cors and not session" -v

# Ou un module spécifique
python -m pytest test/test_models.py -v
```

### Tests de Sécurité Spécifiques

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
# Générer rapport de couverture
python -m pytest test/ --cov=app --cov-report=html

# Ouvrir le rapport
open htmlcov/index.html  # macOS/Linux
start htmlcov\index.html # Windows
```

---

## 📁 Structure des Tests

```
test/
├── test_sql_injection_prevention.py      # 59 tests
├── test_cors_security.py                 # 45 tests
├── test_session_management.py            # 29 tests
├── test_encryption.py                    # 29 tests
├── test_admin_auth.py                    # 29 tests
├── test_models.py                        # 40+ tests
├── test_database.py                      # 30+ tests
├── test_monitoring.py                    # 25+ tests
├── test_routes.py                        # 30+ tests
└── test_audit_logger.py                  # 20+ tests
```

---

## 🔐 Tests de Sécurité Détaillés

### 1️⃣ SQL Injection Prevention (59 tests)

**Fichier:** `test/test_sql_injection_prevention.py`

**Vecteurs testés:**

```python
# UNION-based injection
❌ "SELECT * FROM agents WHERE id = 1 UNION SELECT * FROM users"

# Boolean-based blind injection
❌ "SELECT * FROM agents WHERE id = 1 AND 1=1"

# Time-based blind injection
❌ "SELECT * FROM agents WHERE id = 1; WAITFOR DELAY '00:00:05'"

# Error-based injection
❌ "SELECT * FROM agents WHERE id = EXTRACTVALUE(1, CONCAT(0x7e, ...))"

# Stacked queries
❌ "SELECT * FROM agents; DROP TABLE users;--"

# Comment injection
❌ "SELECT * FROM agents WHERE id = 1 -- comment"

# Wildcard injection
❌ "SELECT * FROM agents WHERE name LIKE '%' OR '1'='1'%"
```

**Tests inclus:**

```
✅ Pattern detection (20 tests)
✅ Parameterized queries (15 tests)
✅ Edge cases & encoding (24 tests)
```

**Résultat:**
```
test_sql_injection_prevention.py::test_union_based PASSED
test_sql_injection_prevention.py::test_boolean_blind PASSED
... (59 tests)
==================== 59 passed ====================
```

---

### 2️⃣ CORS Security (45 tests)

**Fichier:** `test/test_cors_security.py`

**Tests:**

```python
# Origin validation
✅ test_exact_origin_match
✅ test_subdomain_wildcard
✅ test_regex_pattern
✅ test_reject_unauthorized_origin

# Method validation
✅ test_allowed_methods
✅ test_reject_unauthorized_methods

# Dangerous headers
✅ test_filter_authorization_header
✅ test_filter_cookie_header
✅ test_filter_set_cookie_header

# Credentials
✅ test_credentials_allowed
✅ test_credentials_disabled_with_wildcard
```

**Résultat:**
```
test_cors_security.py PASSED [100%]
==================== 45 passed ====================
```

---

### 3️⃣ Session Management & Key Rotation (29 tests)

**Fichier:** `test/test_session_management.py`

**Tests:**

```python
# Session creation & validation
✅ test_create_session
✅ test_validate_valid_session
✅ test_reject_expired_session

# Session regeneration
✅ test_regenerate_session
✅ test_old_session_invalidated

# Key rotation
✅ test_rotate_key
✅ test_old_key_retained
✅ test_max_active_keys_limit

# IP & User-Agent consistency
✅ test_ip_change_detected
✅ test_user_agent_change_detected
```

**Résultat:**
```
test_session_management.py PASSED [100%]
==================== 29 passed ====================
```

---

## 🚀 PowerShell Testing Scripts

Scripts automatisés pour tester l'API:

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

**Résultat:**
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
- Status codes détaillés
- Response bodies (JSON)
- Headers
- Errors avec contexte

**Utile pour:**
- Déboguer les erreurs API
- Vérifier les headers exactes
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

## 🧪 Test-Driven Development (TDD)

### Workflow TDD utilisé

```
1. Écrire un test qui échoue ❌
   ↓
2. Écrire le code minimum pour passer le test ✅
   ↓
3. Refactoriser et améliorer le code 🔄
   ↓
4. Tous les tests continuent de passer ✅
```

### Exemple: SQL Injection Prevention

```python
# 1. Test (écrit d'abord)
def test_union_injection_detected():
    pattern = detect_injection_pattern("SELECT * UNION SELECT * FROM users")
    assert pattern == SQLDangerPattern.UNION_BASED

# 2. Code minimum
def detect_injection_pattern(query: str):
    if "UNION SELECT" in query.upper():
        return SQLDangerPattern.UNION_BASED
    return None

# 3. Refactoriser
# (Implémenter tous les patterns, optimiser regex, etc.)

# 4. Vérifier tous les tests passent
# pytest test/test_sql_injection_prevention.py -v
```

---

## 📈 Coverage

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
# Générer
python -m pytest test/ --cov=app --cov-report=html

# Ouvrir
open htmlcov/index.html
```

---

## 🔍 Debugging Failed Tests

### Étape 1: Voir l'erreur complète

```bash
python -m pytest test/test_sql_injection_prevention.py::test_union_based -v
```

### Étape 2: Mode verbose

```bash
python -m pytest test/ -vv --tb=long
```

### Étape 3: Stop au premier échec

```bash
python -m pytest test/ -x  # Arrête au premier échec
```

### Étape 4: Lancer 1 test spécifique

```bash
python -m pytest test/test_models.py::test_agent_creation -v
```

---

## 🐛 Problèmes Courants

### "ModuleNotFoundError: No module named 'app'"

```bash
# Activer l'environnement virtuel
source venv/bin/activate  # Linux/macOS
. venv\Scripts\Activate.ps1  # Windows
```

### "Cannot connect to database"

```bash
# Les tests utilisent une BD in-memory, vérifier la config .env
cat .env | grep DATABASE_MODE

# Doit être: DATABASE_MODE=memory (pour les tests)
```

### Test timeout (30+ secondes)

```bash
# Utiliser pytest avec timeout
pip install pytest-timeout

python -m pytest test/ --timeout=10
```

---

## ✅ Checklist Pre-Commit

Avant de commiter:

- [ ] Tous les tests passent: `pytest test/ -q`
- [ ] Coverage >95%: `pytest test/ --cov=app`
- [ ] Pas de warnings: `pytest test/ -W error`
- [ ] Code formaté: `black app/ test/`
- [ ] Linting OK: `pylint app/`

---

## 📚 Ressources

- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://testpyramid.com/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

---

## 🚀 Intégration Continue (CI/CD)

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

📖 **Pour plus de détails:** Voir [Testing Scripts Index](../../scripts/README.md)
