# 📜 Scripts d'Automatisation

Tous les scripts PowerShell pour automatiser le déploiement, testing et gestion.

---

## 🚀 Démarrage Rapide

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

# Debug détaillé des erreurs
.\test\debug_api_test.ps1

# Tests complets avec rapport
.\test\test_backend_complete.ps1
```

### Agents

```powershell
# Lancer un agent PowerShell
.\agent\agent_real.ps1

# L'agent s'enregistre automatiquement auprès du serveur
```

---

## 📁 Structure

```
scripts/
├── README.md (ce fichier)
├── server/
│  └── run_server.ps1              # Lancer l'API FastAPI
├── test/
│  ├── test_all.ps1                # Suite complète de tests
│  ├── test_backend_complete.ps1   # Tests détaillés + rapport
│  ├── test_backend_quick.ps1      # Tests rapides
│  ├── quick_api_test.ps1          # Smoke tests (5 tests)
│  └── debug_api_test.ps1          # Tests avec diagnostics détaillés
└── agent/
   └── agent_real.ps1              # Agent PowerShell client
```

---

## 🖥️ Server: `server/run_server.ps1`

Lance le serveur API FastAPI avec configuration complète.

### Usage

```powershell
.\server\run_server.ps1 [options]
```

### Options

| Option | Valeur Par Défaut | Description |
|--------|-------------------|-------------|
| `-Port` | `8000` | Port d'écoute |
| `-Host` | `0.0.0.0` | Interface d'écoute |
| `-Database` | `memory` | Mode base de données (`memory`, `mongodb`) |

### Exemples

```powershell
# Démarrage simple (development)
.\server\run_server.ps1

# Production avec MongoDB
.\server\run_server.ps1 -Port 8000 -Database mongodb

# Interface locale seulement
.\server\run_server.ps1 -Host 127.0.0.1
```

### Résultat Attendu

```
[INFO] Initializing Jadus Audit API
[INFO] Database mode: In-Memory (development)
[INFO] ✅ In-Memory database initialized
[INFO] Setting up CORS with 3 allowed origins
[INFO] Routes registered successfully
[INFO] 
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 🧪 Tests: `test/*`

### `test_all.ps1` - Suite Complète (⏱️ 5 minutes)

Lancer tous les tests: unit tests, API tests, integration tests.

```powershell
.\test\test_all.ps1
```

**Effectue:**
- ✅ pytest (376 tests)
- ✅ Server startup (5 secondes)
- ✅ API health check
- ✅ Documentation Swagger
- ✅ Enrollment endpoint
- ✅ Beacon endpoint
- ✅ Results endpoint
- ✅ Rate limiting
- ✅ Security features
- ✅ Monitoring dashboards

**Résultat:**
```
==== RESULTS ====
376 passed in 21.05s
✅ API is working correctly!
✅ ALL TESTS PASSED!
```

---

### `test_backend_complete.ps1` - Tests Détaillés + Rapport

Tests complets avec résultats détaillés et rapport.

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

**Génère:** Rapport formaté dans le terminal

---

### `test_backend_quick.ps1` - Tests Rapides (⏱️ 2 minutes)

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

### `quick_api_test.ps1` - Smoke Tests (⏱️ 30 secondes)

5 tests essentiels avec identifiants uniques à chaque run.

```powershell
.\quick_api_test.ps1
```

**Tests:**
1. ✅ Health Check
2. ✅ Swagger UI
3. ✅ Agent Enrollment (identifiant unique)
4. ✅ Agent Beacon
5. ✅ Security Headers

**Résultat:** Résumé rapide

```
1. Health Check... [OK] HTTP 200
2. Swagger UI... [OK] HTTP 200
3. Agent Enrollment... [OK] Agent ID: a1b2c3d4-xxxx
4. Agent Beacon... [OK] 2 tasks available
5. Security Headers... [OK] Found 4/4 security headers
```

---

### `debug_api_test.ps1` - Tests avec Diagnostics

Tests avec capture d'erreurs détaillées (verbose).

```powershell
.\debug_api_test.ps1
```

**Sortie:**
- HTTP status codes
- Response bodies (JSON)
- Error messages en détail
- Timestamps

**Utile pour:**
- Déboguer les erreurs API
- Vérifier les headers
- Voir la structure JSON exacte
- Trouver les problèmes de connectivité

---

## 👥 Agent: `agent/agent_real.ps1`

Lance un agent PowerShell qui s'enregistre auprès du serveur.

### Usage

```powershell
.\agent\agent_real.ps1
```

### Processus

```
1. S'enregistre auprès du serveur (POST /api/enroll)
2. Récoit un agent_id + api_key
3. Envoie des heartbeats (POST /api/beacon) toutes les 30s
4. Récoit des tâches du serveur
5. Exécute les tâches PowerShell
6. Envoie les résultats (POST /api/results)
7. Boucle infinie
```

### Résultat Attendu

```
[Agent] Registering with Jadus Audit...
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

## 🔄 Workflow Complet

### Démarrage Normal

**Terminal 1 - Serveur:**
```powershell
cd server_C2
. .\venv\Scripts\Activate.ps1
.\scripts\server\run_server.ps1
```

**Terminal 2 - Tests:**
```powershell
cd server_C2
.\scripts\test\quick_api_test.ps1
```

**Terminal 3 - Agent:**
```powershell
cd server_C2
. .\venv\Scripts\Activate.ps1
.\scripts\agent\agent_real.ps1
```

**Terminal 4 - Dashboard:**
```powershell
cd server_C2/web
python -m http.server 8080
# Accédez à http://localhost:8080
```

---

## 📊 Résumé des Tests

| Script | Durée | Tests | Usefulness |
|--------|-------|-------|-----------|
| `quick_api_test.ps1` | 30 sec | 5 | Vérification rapide |
| `test_backend_quick.ps1` | 2 min | 15 | Validation |
| `debug_api_test.ps1` | 1 min | 7 | Débogage |
| `test_backend_complete.ps1` | 5 min | 30+ | Complet |
| `test_all.ps1` | 5 min | 376 | Exhaustif |

---

## 🐛 Troubleshooting

### "Permission denied"

```powershell
# Autoriser l'exécution
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

### Tests échouent

```powershell
# Lancer le debug
.\scripts\test\debug_api_test.ps1

# Vérifier les logs
tail -f logs/c2_server.log
```

---

## 📚 Documentation Complète

- 📖 [Quick Start](../docs/setup/QUICK_START.md)
- 🏗️ [Architecture](../docs/architecture/ARCHITECTURE.md)
- 🧪 [Testing Guide](../docs/testing/TESTING.md)
- 📡 [API Documentation](../docs/api/API.md)

---

## ✅ Checklist Rapide

Avant d'exécuter les scripts:

- [ ] Python 3.8+ installé
- [ ] Virtual environment activé (`. .\venv\Scripts\Activate.ps1`)
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] `.env` configuré (ENCRYPTION_KEY, CSRF_SECRET_KEY, etc.)
- [ ] Port 8000 disponible (ou utiliser `-Port`)

---

**🎯 Prêt!** Exécutez les scripts selon vos besoins.
