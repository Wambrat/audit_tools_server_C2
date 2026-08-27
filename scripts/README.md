# ðŸ“œ Scripts d'Automatisation

Tous les scripts PowerShell pour automatiser le dÃ©ploiement, testing et gestion.

---

## ðŸš€ DÃ©marrage Rapide

### Serveur

```powershell
# Lancer le serveur API FastAPI
.\server\run_server.ps1

# Avec options
.\server\run_server.ps1 -Port 8001 -Host 0.0.0.0 -Database mongodb
```

### Tests

```powershell
# Tous les tests backend
.\test\test_all.ps1

# Tests rapides (smoke tests)
.\test\quick_api_test.ps1

# Debug dÃ©taillÃ© des erreurs
.\test\debug_api_test.ps1

# Tests complets avec rapport
.\test\test_backend_complete.ps1
```

### Agents

```powershell
# Lancer un agent PowerShell
.\agent\agent_real.ps1

# L'agent s'enregistre automatiquement auprÃ¨s du serveur
```

---

## ðŸ“ Structure

```
scripts/
â”œâ”€â”€ README.md (ce fichier)
â”œâ”€â”€ server/
â”‚  â””â”€â”€ run_server.ps1              # Lancer l'API FastAPI
â”œâ”€â”€ test/
â”‚  â”œâ”€â”€ test_all.ps1                # Suite complÃ¨te de tests
â”‚  â”œâ”€â”€ test_backend_complete.ps1   # Tests dÃ©taillÃ©s + rapport
â”‚  â”œâ”€â”€ test_backend_quick.ps1      # Tests rapides
â”‚  â”œâ”€â”€ quick_api_test.ps1          # Smoke tests (5 tests)
â”‚  â””â”€â”€ debug_api_test.ps1          # Tests avec diagnostics dÃ©taillÃ©s
â””â”€â”€ agent/
   â””â”€â”€ agent_real.ps1              # Agent PowerShell client
```

---

## ðŸ–¥ï¸ Server: `server/run_server.ps1`

Lance le serveur API FastAPI avec configuration complÃ¨te.

### Usage

```powershell
.\server\run_server.ps1 [options]
```

### Options

| Option | Valeur Par DÃ©faut | Description |
|--------|-------------------|-------------|
| `-Port` | `8000` | Port d'Ã©coute |
| `-Host` | `0.0.0.0` | Interface d'Ã©coute |
| `-Database` | `memory` | Mode base de donnÃ©es (`memory`, `mongodb`) |

### Exemples

```powershell
# DÃ©marrage simple (development)
.\server\run_server.ps1

# Production avec MongoDB
.\server\run_server.ps1 -Port 8000 -Database mongodb

# Interface locale seulement
.\server\run_server.ps1 -Host 127.0.0.1
```

### RÃ©sultat Attendu

```
[INFO] Initializing jadus Server API
[INFO] Database mode: In-Memory (development)
[INFO] âœ… In-Memory database initialized
[INFO] Setting up CORS with 3 allowed origins
[INFO] Routes registered successfully
[INFO] 
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## ðŸ§ª Tests: `test/*`

### `test_all.ps1` - Suite ComplÃ¨te (â±ï¸ 5 minutes)

Lancer tous les tests: unit tests, API tests, integration tests.

```powershell
.\test\test_all.ps1
```

**Effectue:**
- âœ… pytest (376 tests)
- âœ… Server startup (5 secondes)
- âœ… API health check
- âœ… Documentation Swagger
- âœ… Enrollment endpoint
- âœ… Beacon endpoint
- âœ… Results endpoint
- âœ… Rate limiting
- âœ… Security features
- âœ… Monitoring dashboards

**RÃ©sultat:**
```
==== RESULTS ====
376 passed in 21.05s
âœ… API is working correctly!
âœ… ALL TESTS PASSED!
```

---

### `test_backend_complete.ps1` - Tests DÃ©taillÃ©s + Rapport

Tests complets avec rÃ©sultats dÃ©taillÃ©s et rapport.

```powershell
.\test\test_backend_complete.ps1
```

**Tests:**
1. Unit tests (pytest)
2. Server startup
3. API documentation (/docs)
4. Endpoints (enroll, beacon, results)
5. Rate limiting
6. Security features
7. Integration tests
8. Logs

**GÃ©nÃ¨re:** Rapport formatÃ© dans le terminal

---

### `test_backend_quick.ps1` - Tests Rapides (â±ï¸ 2 minutes)

Version rapide pour validation rapide.

```powershell
.\test\test_backend_quick.ps1
```

**Tests:**
1. Unit tests
2. Server startup
3. Health check
4. Swagger UI
5. API enrollment

---

### `quick_api_test.ps1` - Smoke Tests (â±ï¸ 30 secondes)

5 tests essentiels avec identifiants uniques Ã  chaque run.

```powershell
.\quick_api_test.ps1
```

**Tests:**
1. âœ… Health Check
2. âœ… Swagger UI
3. âœ… Agent Enrollment (identifiant unique)
4. âœ… Agent Beacon
5. âœ… Security Headers

**RÃ©sultat:** RÃ©sumÃ© rapide

```
1. Health Check... [OK] HTTP 200
2. Swagger UI... [OK] HTTP 200
3. Agent Enrollment... [OK] Agent ID: a1b2c3d4-xxxx
4. Agent Beacon... [OK] 2 tasks available
5. Security Headers... [OK] Found 4/4 security headers
```

---

### `debug_api_test.ps1` - Tests avec Diagnostics

Tests avec capture d'erreurs dÃ©taillÃ©es (verbose).

```powershell
.\debug_api_test.ps1
```

**Sortie:**
- HTTP status codes
- Response bodies (JSON)
- Error messages en dÃ©tail
- Timestamps

**Utile pour:**
- DÃ©boguer les erreurs API
- VÃ©rifier les headers
- Voir la structure JSON exacte
- Trouver les problÃ¨mes de connectivitÃ©

---

## ðŸ‘¥ Agent: `agent/agent_real.ps1`

Lance un agent PowerShell qui s'enregistre auprÃ¨s du serveur.

### Usage

```powershell
.\agent\agent_real.ps1
```

### Processus

```
1. S'enregistre auprÃ¨s du serveur (POST /api/enroll)
2. RÃ©coit un agent_id + api_key
3. Envoie des heartbeats (POST /api/beacon) toutes les 30s
4. RÃ©coit des tÃ¢ches du serveur
5. ExÃ©cute les tÃ¢ches PowerShell
6. Envoie les rÃ©sultats (POST /api/results)
7. Boucle infinie
```

### RÃ©sultat Attendu

```
[Agent] Registering with jadus Server...
[Agent] Successfully registered!
[Agent] Agent ID: a1b2c3d4-...
[Agent] API Key: sk_xxxxx...
[Agent] Status: ACTIVE
[Agent] Listening for commands...

[Beacon] Heartbeat #1 OK, 0 tasks
[Beacon] Heartbeat #2 OK, 1 task received
[Task] Executing: Get-Process
[Result] Task completed, sending result...
[Beacon] Heartbeat #3 OK, 0 tasks
```

---

## ðŸ”„ Workflow Complet

### DÃ©marrage Normal

**Terminal 1 - Serveur:**
```powershell
cd jadus
. .\venv\Scripts\Activate.ps1
.\scripts\server\run_server.ps1
```

**Terminal 2 - Tests:**
```powershell
cd jadus
.\scripts\test\quick_api_test.ps1
```

**Terminal 3 - Agent:**
```powershell
cd jadus
. .\venv\Scripts\Activate.ps1
.\scripts\agent\agent_real.ps1
```

**Terminal 4 - Dashboard:**
```powershell
cd jadus/web
python -m http.server 8080
# AccÃ©dez Ã  http://localhost:8080
```

---

## ðŸ“Š RÃ©sumÃ© des Tests

| Script | DurÃ©e | Tests | Usefulness |
|--------|-------|-------|-----------|
| `quick_api_test.ps1` | 30 sec | 5 | VÃ©rification rapide |
| `test_backend_quick.ps1` | 2 min | 15 | Validation |
| `debug_api_test.ps1` | 1 min | 7 | DÃ©bogage |
| `test_backend_complete.ps1` | 5 min | 30+ | Complet |
| `test_all.ps1` | 5 min | 376 | Exhaustif |

---

## ðŸ› Troubleshooting

### "Permission denied"

```powershell
# Autoriser l'exÃ©cution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Python not found"

```powershell
# Activer l'environnement virtuel
. .\venv\Scripts\Activate.ps1
```

### "Port 8000 already in use"

```powershell
# Utiliser un autre port
.\scripts\server\run_server.ps1 -Port 8001
```

### Tests Ã©chouent

```powershell
# Lancer le debug
.\scripts\test\debug_api_test.ps1

# VÃ©rifier les logs
tail -f logs/jadus_server.log
```

---

## ðŸ“š Documentation ComplÃ¨te

- ðŸ“– [Quick Start](../docs/setup/QUICK_START.md)
- ðŸ—ï¸ [Architecture](../docs/architecture/ARCHITECTURE.md)
- ðŸ§ª [Testing Guide](../docs/testing/TESTING.md)
- ðŸ“¡ [API Documentation](../docs/api/API.md)

---

## âœ… Checklist Rapide

Avant d'exÃ©cuter les scripts:

- [ ] Python 3.8+ installÃ©
- [ ] Virtual environment activÃ© (`. .\venv\Scripts\Activate.ps1`)
- [ ] DÃ©pendances installÃ©es (`pip install -r requirements.txt`)
- [ ] `.env` configurÃ© (ENCRYPTION_KEY, CSRF_SECRET_KEY, etc.)
- [ ] Port 8000 disponible (ou utiliser `-Port`)

---

**ðŸŽ¯ PrÃªt!** ExÃ©cutez les scripts selon vos besoins.

