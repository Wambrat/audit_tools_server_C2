# 📡 API Documentation

Documentation complète des endpoints de l'API C2 Server.

---

## 🚀 Accès Rapide

**API accessible sur:** `http://localhost:8000`

**Documentation interactive (Swagger UI):** `http://localhost:8000/docs`

**ReDoc (documentation belle):** `http://localhost:8000/redoc`

**OpenAPI 3.0 Schema:** `http://localhost:8000/openapi.json`

---

## 🔑 Authentification

### Agent Authentication (API Key)

Les agents s'authentifient avec `agent_id + api_key`:

```bash
curl -X POST http://localhost:8000/api/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "AGENT-01",
    "os_version": "Windows 10",
    "hostname": "PC-001",
    "username": "admin"
  }'

# Réponse
{
  "agent_id": "a1b2c3d4-...",
  "api_key": "sk_xxxxxxxxxxxxxxxx",
  "message": "Agent enrolled successfully"
}
```

Utiliser ensuite l'`agent_id` et `api_key` dans les headers:

```bash
curl -X POST http://localhost:8000/api/beacon \
  -H "Content-Type: application/json" \
  -H "X-Agent-ID: a1b2c3d4-..." \
  -H "X-API-Key: sk_xxxxxxxxxxxxxxxx" \
  -d '{
    "status": "healthy",
    "uptime_seconds": 3600
  }'
```

### Admin Authentication (JWT)

Les administrateurs s'authentifient avec JWT pour accéder au monitoring:

```bash
# 1. Connexion
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "changeme"
  }'

# Réponse
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}

# 2. Utilisation du token
curl http://localhost:8000/api/monitoring/overview \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## 📋 Endpoints par Catégorie

### 👥 Agents (6 endpoints)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **POST** | `/api/enroll` | Enregistrer un nouvel agent | Aucune (rate limited) |
| **GET** | `/api/agents` | Lister tous les agents | Agent |
| **GET** | `/api/agents/{agent_id}` | Détails d'un agent | Agent |
| **GET** | `/api/beacon-history/{agent_id}` | Historique des beacons | Agent |
| **GET** | `/api/beacon-stats/{agent_id}` | Statistiques des beacons | Agent |

### 🎯 Tâches (2 endpoints)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **GET** | `/api/tasks/{agent_id}` | Lister les tâches en attente | Agent |
| **POST** | `/api/tasks/{agent_id}` | Créer une nouvelle tâche | Agent |

### 📊 Résultats (3 endpoints)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **POST** | `/api/results` | Soumettre un résultat d'audit | Agent |
| **GET** | `/api/results/{agent_id}` | Lister les résultats d'un agent | Agent |
| **GET** | `/api/results/{agent_id}/{result_id}` | Détails d'un résultat | Agent |

### 📈 Monitoring (6 endpoints)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **GET** | `/api/monitoring/overview` | Vue d'ensemble du système | JWT Admin |
| **GET** | `/api/monitoring/agents` | Dashboard des agents | JWT Admin |
| **GET** | `/api/monitoring/tasks` | Dashboard des tâches | JWT Admin |
| **GET** | `/api/monitoring/results` | Dashboard des résultats | JWT Admin |
| **GET** | `/api/monitoring/alerts` | Alertes système | JWT Admin |
| **GET** | `/api/monitoring/dashboard` | Tout combiné | JWT Admin |

### 🔧 Utilitaires

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| **GET** | `/health` | Health check | Aucune |
| **POST** | `/api/admin/login` | Admin login | Aucune |

---

## 📌 Détails des Endpoints

### 1️⃣ POST /api/enroll

Enregistrer un nouvel agent.

**Requête:**
```json
{
  "agent_name": "AGENT-01",
  "os_version": "Windows 10",
  "hostname": "PC-001",
  "username": "admin"
}
```

**Réponse (200 OK):**
```json
{
  "agent_id": "a1b2c3d4-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
  "api_key": "sk_1234567890abcdefghijklmnop",
  "message": "Agent enrolled successfully"
}
```

**Codes Possibles:**
- `200 OK` - Agent enregistré avec succès
- `409 Conflict` - Agent déjà enregistré (même hostname:username)
- `429 Too Many Requests` - Rate limit dépassé (5 requêtes/heure)
- `422 Unprocessable Entity` - Données manquantes ou invalides

**Rate Limit:** 5 requêtes/heure par adresse IP

---

### 2️⃣ POST /api/beacon

Envoyer un heartbeat (signal de vie).

**Requête:**
```json
{
  "agent_id": "a1b2c3d4-...",
  "api_key": "sk_...",
  "status": "healthy",
  "uptime_seconds": 3600
}
```

**Réponse (200 OK):**
```json
{
  "message": "Beacon received",
  "tasks": [
    {
      "task_id": "task-001",
      "command": "Get-Process",
      "priority": "high",
      "timeout_seconds": 300
    }
  ],
  "next_beacon_interval": 30
}
```

**Codes Possibles:**
- `200 OK` - Beacon accepté
- `401 Unauthorized` - agent_id ou api_key invalide
- `429 Too Many Requests` - Rate limit dépassé (100 requêtes/heure)
- `422 Unprocessable Entity` - Données manquantes

**Rate Limit:** 100 requêtes/heure par agent

---

### 3️⃣ POST /api/results

Soumettre les résultats d'une tâche.

**Requête:**
```json
{
  "agent_id": "a1b2c3d4-...",
  "api_key": "sk_...",
  "task_id": "task-001",
  "status": "success",
  "output": {
    "processes": [
      {"name": "notepad.exe", "pid": 1234},
      {"name": "cmd.exe", "pid": 5678}
    ]
  },
  "execution_time_ms": 1250
}
```

**Réponse (200 OK):**
```json
{
  "result_id": "result-...",
  "message": "Result received and stored",
  "encrypted": true
}
```

**Codes Possibles:**
- `200 OK` - Résultat stocké
- `401 Unauthorized` - Authentification échouée
- `404 Not Found` - Task ID invalide
- `413 Payload Too Large` - Résultat trop volumineux
- `429 Too Many Requests` - Rate limit (50 requêtes/heure)

**Rate Limit:** 50 requêtes/heure par agent

---

### 4️⃣ GET /api/monitoring/overview

Vue d'ensemble du système (Admin uniquement).

**Authentification:** JWT Bearer token requis

**Réponse (200 OK):**
```json
{
  "agents": {
    "total": 25,
    "active": 23,
    "inactive": 2
  },
  "tasks": {
    "total": 150,
    "pending": 10,
    "assigned": 5,
    "completed": 130,
    "failed": 5
  },
  "results": {
    "total": 480,
    "success": 450,
    "failed": 30,
    "success_rate": 0.9375
  },
  "execution_time_avg_ms": 1250
}
```

---

### 5️⃣ GET /api/monitoring/alerts

Alertes système (Admin uniquement).

**Authentification:** JWT Bearer token requis

**Réponse (200 OK):**
```json
{
  "overall_level": "warning",
  "critical_alerts": 0,
  "warning_alerts": 2,
  "alerts": [
    {
      "level": "warning",
      "type": "agent_slow",
      "agent_id": "a1b2c3d4-...",
      "agent_name": "AGENT-05",
      "message": "Agent slow: no beacon for 45 minutes",
      "timestamp": "2026-06-16T17:45:00Z"
    },
    {
      "level": "warning",
      "type": "task_timeout",
      "task_id": "task-001",
      "message": "Task timeout: execution exceeded 300s",
      "timestamp": "2026-06-16T17:30:00Z"
    }
  ]
}
```

---

## 🔐 Sécurité

### Rate Limiting

L'API implémente un rate limiting par agent:

- **Enroll:** 5 requêtes/heure
- **Beacon:** 100 requêtes/heure
- **Results:** 50 requêtes/heure
- **Admin Login:** 5 tentatives/heure

**Réponse rate limit (429):**
```json
{
  "detail": "Too many requests. Max 5 per 3600s"
}
```

### SQL Injection Prevention

L'API détecte et bloque les tentatives d'injection SQL:

```
❌ GET /api/agents?name=' OR '1'='1
HTTP 400 Bad Request
{
  "detail": "Injection pattern detected: UNION_BASED"
}
```

### CORS Security

Requêtes autorisées depuis:
- `http://localhost:3000` (dev frontend)
- `http://localhost:5500` (Live Server)
- `http://127.0.0.1:8000` (API self)

### Security Headers

Toutes les réponses incluent:
- `Strict-Transport-Security`: Force HTTPS
- `Content-Security-Policy`: Restreint les ressources
- `X-Frame-Options`: DENY (prévient le clickjacking)
- `X-Content-Type-Options`: nosniff (MIME sniffing)

---

## 📚 Modèles de Données

### Agent
```json
{
  "agent_id": "uuid",
  "agent_name": "string",
  "hostname": "string",
  "username": "string",
  "os_version": "string",
  "api_key": "string",
  "status": "active|inactive|compromised",
  "created_at": "2026-06-16T10:00:00Z",
  "last_beacon": "2026-06-16T17:45:00Z"
}
```

### Task
```json
{
  "task_id": "uuid",
  "agent_id": "uuid",
  "command": "string",
  "priority": "low|medium|high",
  "status": "pending|assigned|completed|failed",
  "assigned_at": "2026-06-16T17:45:00Z",
  "timeout_seconds": 300
}
```

### AuditResult
```json
{
  "result_id": "uuid",
  "task_id": "uuid",
  "agent_id": "uuid",
  "status": "success|failed|timeout",
  "output": {},
  "execution_time_ms": 1250,
  "submitted_at": "2026-06-16T17:46:00Z"
}
```

---

## 🧪 Exemples PowerShell

### Enregistrer un Agent

```powershell
$body = @{
    agent_name = "AUDIT-PC-01"
    os_version = "Windows 10 Pro"
    hostname = "DESKTOP-ABC123"
    username = "DOMAIN\admin"
} | ConvertTo-Json

$response = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/enroll" `
    -Method POST `
    -Headers @{"Content-Type" = "application/json"} `
    -Body $body

$response | ConvertTo-Json
```

### Envoyer un Beacon

```powershell
$body = @{
    agent_id = $response.agent_id
    api_key = $response.api_key
    status = "healthy"
    uptime_seconds = 3600
} | ConvertTo-Json

$beacon = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/beacon" `
    -Method POST `
    -Headers @{"Content-Type" = "application/json"} `
    -Body $body

$beacon | ConvertTo-Json
```

---

## 📖 Documentation Complète

- 📚 [Architecture](../architecture/ARCHITECTURE.md)
- 🔐 [Sécurité](../architecture/SECURITY.md)
- 🧪 [Tests](../testing/TESTING.md)
- 🚀 [Quick Start](../setup/QUICK_START.md)

---

**Last Updated:** 2026-06-16

Pour plus de détails, accédez à la documentation interactive Swagger UI: `http://localhost:8000/docs`
