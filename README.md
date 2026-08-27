# jadus Server API - Python FastAPI

API REST pour gÃ©rer et coordonner les agents PowerShell d'audit de sÃ©curitÃ©.

## Architecture

```
jadus/
â”œâ”€â”€ app/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ models.py          # ModÃ¨les Pydantic (requÃªtes/rÃ©ponses)
â”‚   â”œâ”€â”€ database.py        # Gestion de la base de donnÃ©es
â”‚   â”œâ”€â”€ auth.py            # Authentification des agents
â”‚   â”œâ”€â”€ routes.py          # Endpoints (routes)
â”‚   â”œâ”€â”€ logger.py          # SystÃ¨me de logging structurÃ©
â”‚   â”œâ”€â”€ rate_limiter.py    # Rate limiting par agent/endpoint
â”‚   â””â”€â”€ monitoring.py      # Monitoring et dashboards
â”œâ”€â”€ web/                   # Application Vue.js (frontend)
â”‚   â”œâ”€â”€ index.html         # Interface principale
â”‚   â”œâ”€â”€ js/
â”‚   â”‚   â”œâ”€â”€ api.js        # Client API
â”‚   â”‚   â””â”€â”€ app.js        # Application Vue
â”‚   â”œâ”€â”€ css/
â”‚   â”‚   â””â”€â”€ style.css     # Styles
â”‚   â””â”€â”€ README.md         # Documentation web
â”œâ”€â”€ main.py                # Point d'entrÃ©e FastAPI
â”œâ”€â”€ requirements.txt       # DÃ©pendances Python
â”œâ”€â”€ .env                   # Variables d'environnement
â”œâ”€â”€ .gitignore
â””â”€â”€ README.md             # Ce fichier
```

## Installation

### 1. CrÃ©er un environnement virtuel Python

```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

### 2. Installer les dÃ©pendances

```bash
pip install -r requirements.txt
```

### 3. Lancer le serveur

```bash
python main.py
# Ou directement avec uvicorn:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Le serveur dÃ©marre sur `http://localhost:8000`

### Documentation interactive

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### 1. **POST /api/enroll** - Enregistrement d'un agent

PremiÃ¨re connexion de l'agent pour recevoir son ID unique et sa clÃ© API.

**RequÃªte:**
```json
{
  "agent_name": "AUDIT-AGENT-01",
  "os_version": "Windows 10 Enterprise",
  "hostname": "SERVER-01",
  "username": "SYSTEM"
}
```

**RÃ©ponse (200):**
```json
{
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "api_key": "f1e2d3c4-b5a6-7890-cdef-1234567890ab",
  "message": "Agent AUDIT-AGENT-01 enrolled successfully"
}
```

---

### 2. **POST /api/beacon** - Heartbeat + RÃ©cupÃ©ration des tÃ¢ches

L'agent envoie son Ã©tat et reÃ§oit les tÃ¢ches en attente.

**RequÃªte:**
```json
{
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "api_key": "f1e2d3c4-b5a6-7890-cdef-1234567890ab",
  "status": "online",
  "last_task_id": null,
  "uptime_seconds": 3600
}
```

**RÃ©ponse (200):**
```json
{
  "tasks": [
    {
      "task_id": "task-001",
      "command": "Get-Process",
      "parameters": null,
      "priority": 0,
      "timeout_seconds": 300
    }
  ],
  "next_beacon_interval": 30
}
```

---

### 3. **POST /api/results** - Envoi des rÃ©sultats d'audit

L'agent envoie le compte-rendu d'une tÃ¢che complÃ©tÃ©e.

**RequÃªte:**
```json
{
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "api_key": "f1e2d3c4-b5a6-7890-cdef-1234567890ab",
  "task_id": "task-001",
  "status": "success",
  "result": {
    "processes": [
      {"name": "notepad.exe", "pid": 1234},
      {"name": "cmd.exe", "pid": 5678}
    ]
  },
  "execution_time_ms": 245,
  "error_message": null
}
```

**RÃ©ponse (200):**
```json
{
  "message": "Result for task task-001 acknowledged",
  "acknowledged": true
}
```

---

## Endpoints de gestion (pour les tests/debug)

### GET /api/agents
Lister tous les agents enregistrÃ©s.

### GET /api/tasks/{agent_id}
Lister les tÃ¢ches d'un agent.

### POST /api/tasks/{agent_id}
CrÃ©er une nouvelle tÃ¢che pour un agent.

**ParamÃ¨tres:**
- `command`: Commande Ã  exÃ©cuter
- `parameters`: ParamÃ¨tres optionnels
- `priority`: PrioritÃ© de la tÃ¢che (0 = normal)

### GET /api/results/{agent_id}
RÃ©cupÃ©rer tous les rÃ©sultats d'un agent.

---

## Flux de fonctionnement

```
1. ENROLL (premiÃ¨re connexion)
   Agent â†’ POST /api/enroll â†’ ReÃ§oit agent_id + api_key

2. BEACON (heartbeat + rÃ©cupÃ©ration des tÃ¢ches)
   Agent â†’ POST /api/beacon (toutes les 30s) â†’ ReÃ§oit les tÃ¢ches
   
3. EXECUTE (agent exÃ©cute les tÃ¢ches)
   Agent exÃ©cute localement (PowerShell)
   
4. RESULTS (envoi des rÃ©sultats)
   Agent â†’ POST /api/results â†’ Serveur enregistre le rÃ©sultat
```

---

## Authentification

Chaque requÃªte (sauf `/api/enroll`) doit incluire:
- `agent_id`: Identifiant unique de l'agent
- `api_key`: ClÃ© API fournie lors de l'enregistrement

---

## Base de donnÃ©es

### Configuration Actuelle: MongoDB (Persistant)

L'API utilise **MongoDB** pour stocker les donnÃ©es de maniÃ¨re persistante.

**Avantages de MongoDB pour un EDR:**
- âœ… SchÃ©ma flexible (rÃ©sultats d'audit avec structures variÃ©es)
- âœ… JSON natif (PowerShell retourne du JSON)
- âœ… ScalabilitÃ© (100+ agents sans problÃ¨me)
- âœ… Index automatiques (performant)

**Fichiers:**
- [app/database_mongodb.py](app/database_mongodb.py) - Couche MongoDB
- [migrate_to_mongodb.py](migrate_to_mongodb.py) - Script de migration
- [MONGODB_SETUP.md](MONGODB_SETUP.md) - Guide installation MongoDB

**Installation rapide:**
```bash
# Avec Docker (recommandÃ©)
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Puis installer les dÃ©pendances
pip install -r requirements.txt  # Contient pymongo

# Mettre Ã  jour .env
DATABASE_MODE=mongodb
MONGODB_URL=mongodb://localhost:27017
```

ðŸ“– **Guide complet:** [MONGODB_SETUP.md](MONGODB_SETUP.md)

---

## Structure des modÃ¨les de donnÃ©es

### Agent
- `agent_id`: UUID unique
- `api_key`: ClÃ© d'authentification
- `agent_name`: Nom de l'agent
- `os_version`: Version de l'OS
- `hostname`: Hostname du serveur
- `username`: Utilisateur connectÃ©
- `status`: ACTIVE/INACTIVE/COMPROMISED
- `created_at`: Date d'enregistrement
- `last_beacon`: Dernier beacon reÃ§u

### Task
- `task_id`: UUID unique
- `agent_id`: Agent destinataire
- `command`: Commande Ã  exÃ©cuter
- `parameters`: ParamÃ¨tres JSON
- `priority`: PrioritÃ© (0 = normal)
- `status`: PENDING/ASSIGNED/COMPLETED/FAILED
- `timeout_seconds`: Timeout d'exÃ©cution
- `created_at`, `assigned_at`, `completed_at`: Timestamps

### AuditResult
- `result_id`: UUID unique
- `task_id`: TÃ¢che associÃ©e
- `agent_id`: Agent source
- `status`: "success" ou "failed"
- `result`: DonnÃ©es du rÃ©sultat (JSON)
- `execution_time_ms`: Temps d'exÃ©cution
- `error_message`: Message d'erreur (si applicable)
- `created_at`: Timestamp

---

## Variables d'environnement

```env
HOST=0.0.0.0              # Interface d'Ã©coute
PORT=8000                 # Port du serveur
ENV=development           # Mode (development/production)
ALLOWED_ORIGINS=...       # Domaines CORS autorisÃ©s
LOG_LEVEL=INFO            # Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Rate Limiting
ENROLL_RATE_LIMIT=5       # Max 5 enrollements
ENROLL_WINDOW_SECONDS=3600  # Par heure

BEACON_RATE_LIMIT=100     # Max 100 beacons
BEACON_WINDOW_SECONDS=3600  # Par heure

RESULTS_RATE_LIMIT=50     # Max 50 soumissions de rÃ©sultats
RESULTS_WINDOW_SECONDS=3600  # Par heure
```

---

## Rate Limiting

L'API implÃ©mente un systÃ¨me de **rate limiting par agent et par endpoint** pour prÃ©venir les abus et les attaques par dÃ©bordement.

### Fonctionnement

- **Sliding Window**: Les requÃªtes sont comptÃ©es dans une fenÃªtre de temps glissante
- **Par endpoint**: Limites diffÃ©rentes pour enroll, beacon, et results
- **Par agent**: Chaque agent a un compteur indÃ©pendant
- **RÃ©ponse 429**: RetournÃ©e si le limit est dÃ©passÃ©

### Limites par dÃ©faut

| Endpoint | Limite | FenÃªtre |
|----------|--------|---------|
| `/api/enroll` | 5 requÃªtes | 1 heure |
| `/api/beacon` | 100 requÃªtes | 1 heure |
| `/api/results` | 50 requÃªtes | 1 heure |

### RÃ©ponse lors du dÃ©passement

```json
{
  "detail": "Too many beacon requests. Max 100 per 3600s"
}
```

HTTP Status: **429 Too Many Requests**

### Monitoring des limites

Endpoint pour consulter les stats de rate limiting:

```bash
GET /api/rate-limit/stats/{agent_id}/{endpoint}
```

**Exemple de rÃ©ponse:**
```json
{
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "endpoint": "beacon",
  "total_requests": 45,
  "last_request": "2026-05-28T12:34:56.789012",
  "requests_in_last_hour": 45
}
```

---

### Avec cURL

```bash
# Enregistrer un agent
curl -X POST http://localhost:8000/api/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "AUDIT-01",
    "os_version": "Windows 10",
    "hostname": "SERVER-01",
    "username": "SYSTEM"
  }'

# Beacon
curl -X POST http://localhost:8000/api/beacon \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "...",
    "api_key": "...",
    "status": "online",
    "uptime_seconds": 3600
  }'
```

### Avec Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Enroll
response = requests.post(f"{BASE_URL}/enroll", json={
    "agent_name": "AUDIT-01",
    "os_version": "Windows 10",
    "hostname": "SERVER-01",
    "username": "SYSTEM"
})
agent_data = response.json()

# Beacon
response = requests.post(f"{BASE_URL}/beacon", json={
    "agent_id": agent_data["agent_id"],
    "api_key": agent_data["api_key"],
    "status": "online",
    "uptime_seconds": 3600
})
tasks = response.json()
```

---

## Historique des Beacons

L'API enregistre automatiquement chaque **beacon** (connexion/heartbeat) d'un agent pour tracer son activitÃ© au fil du temps.

### DonnÃ©es enregistrÃ©es par beacon

- `beacon_id`: Identifiant unique du beacon
- `agent_id`: Agent source
- `beacon_status`: Ã‰tat signalÃ© par l'agent (online, offline, etc.)
- `uptime_seconds`: Uptime de l'agent
- `tasks_count`: Nombre de tÃ¢ches assignÃ©es
- `ip_address`: IP source (optionnel)
- `created_at`: Timestamp du beacon

### Endpoints d'historique

#### GET /api/beacon-history/{agent_id}

RÃ©cupÃ©rer les derniers beacons d'un agent.

**ParamÃ¨tres:**
- `agent_id`: ID de l'agent
- `limit`: Nombre de beacons Ã  retourner (dÃ©faut: 100, max: 1000)

**Exemple:**
```bash
curl http://localhost:8000/api/beacon-history/a1b2c3d4-... -G -d "limit=50"
```

**RÃ©ponse:**
```json
{
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "beacon_count": 50,
  "beacons": [
    {
      "beacon_id": "beacon-001",
      "beacon_status": "online",
      "uptime_seconds": 86400,
      "tasks_count": 3,
      "ip_address": "192.168.1.100",
      "created_at": "2026-05-28T14:30:00.000000"
    },
    {
      "beacon_id": "beacon-002",
      "beacon_status": "online",
      "uptime_seconds": 86430,
      "tasks_count": 2,
      "ip_address": "192.168.1.100",
      "created_at": "2026-05-28T14:29:30.000000"
    }
  ]
}
```

#### GET /api/beacon-stats/{agent_id}

RÃ©cupÃ©rer les statistiques globales de beacon pour un agent.

**ParamÃ¨tres:**
- `agent_id`: ID de l'agent

**RÃ©ponse:**
```json
{
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "total_beacons": 450,
  "first_beacon": "2026-05-01T10:00:00.000000",
  "last_beacon": "2026-05-28T14:30:00.000000",
  "avg_uptime_seconds": 85200,
  "total_tasks_received": 1250
}
```

### Cas d'usage

**Tracer l'activitÃ© d'un agent:**
```python
import requests

agent_id = "a1b2c3d4-..."

# RÃ©cupÃ©rer les 10 derniers beacons
response = requests.get(f"http://localhost:8000/api/beacon-history/{agent_id}", 
                       params={"limit": 10})
beacons = response.json()["beacons"]

# Analyser la disponibilitÃ©
print(f"DerniÃ¨re connexion: {beacons[0]['created_at']}")
print(f"Uptime moyen: {beacons[0]['uptime_seconds'] / 3600:.1f} heures")
```

**DÃ©tecter les agents inactifs:**
```python
import requests
from datetime import datetime, timedelta

agent_id = "a1b2c3d4-..."

response = requests.get(f"http://localhost:8000/api/beacon-history/{agent_id}",
                       params={"limit": 1})
last_beacon = response.json()["beacons"][0]

last_seen = datetime.fromisoformat(last_beacon["created_at"])
time_since = datetime.now() - last_seen

if time_since > timedelta(hours=1):
    print(f"Agent inactif depuis {time_since}")
```

---

## Monitoring et Dashboard

L'API fournit des **endpoints de monitoring et de dashboard** pour surveiller l'Ã©tat global du systÃ¨me, les agents, tÃ¢ches et rÃ©sultats en temps rÃ©el.

### Vue d'ensemble du systÃ¨me

#### GET /api/monitoring/overview

RÃ©cupÃ©rer une vue d'ensemble des statistiques globales.

**RÃ©ponse:**
```json
{
  "timestamp": "2026-05-28T14:35:00.000000",
  "agents": {
    "total": 12,
    "by_status": {
      "active": 10,
      "inactive": 2,
      "compromised": 0
    }
  },
  "tasks": {
    "total": 45,
    "by_status": {
      "pending": 5,
      "assigned": 8,
      "completed": 30,
      "failed": 2
    }
  },
  "results": {
    "total": 32,
    "by_status": {
      "success": 30,
      "failed": 2
    },
    "avg_execution_time_ms": 245.5
  }
}
```

### Dashboard des agents

#### GET /api/monitoring/agents

RÃ©cupÃ©rer le dashboard dÃ©taillÃ© de tous les agents.

**RÃ©ponse:**
```json
{
  "timestamp": "2026-05-28T14:35:00.000000",
  "total_agents": 12,
  "agents": [
    {
      "agent_id": "a1b2c3d4-...",
      "agent_name": "AUDIT-01",
      "hostname": "SERVER-01",
      "username": "SYSTEM",
      "status": "active",
      "os_version": "Windows 10 Enterprise",
      "is_inactive": false,
      "created_at": "2026-05-01T10:00:00.000000",
      "last_beacon": "2026-05-28T14:30:00.000000",
      "beacon_stats": {
        "total_beacons": 450,
        "first_beacon": "2026-05-01T10:00:00.000000",
        "last_beacon": "2026-05-28T14:30:00.000000",
        "avg_uptime_seconds": 85200,
        "total_tasks_received": 1250
      },
      "tasks": {
        "pending": 2,
        "assigned": 1,
        "completed": 25,
        "failed": 1
      },
      "results_count": 27,
      "success_rate": 92.6
    }
  ]
}
```

**DÃ©tection d'inactivitÃ©:**
- `is_inactive = true` si dernier beacon > 1 heure
- Utile pour identifier les agents en problÃ¨me

### Dashboard des tÃ¢ches

#### GET /api/monitoring/tasks

RÃ©cupÃ©rer le dashboard des tÃ¢ches avec dÃ©tection de problÃ¨mes.

**RÃ©ponse:**
```json
{
  "timestamp": "2026-05-28T14:35:00.000000",
  "total_tasks": 45,
  "by_status": {
    "pending": 5,
    "assigned": 8,
    "completed": 30,
    "failed": 2
  },
  "avg_execution_time_seconds": 15.2,
  "overdue_tasks_count": 2,
  "overdue_task_ids": ["task-001", "task-002"],
  "tasks_by_agent": {
    "a1b2c3d4-...": {
      "count": 29,
      "tasks": [...]
    }
  }
}
```

**DÃ©tection des tÃ¢ches en retard:**
- TÃ¢ches assignÃ©es depuis plus longtemps que leur timeout
- Identifie les blocages potentiels

### Dashboard des rÃ©sultats

#### GET /api/monitoring/results

RÃ©cupÃ©rer le dashboard des rÃ©sultats et taux de succÃ¨s.

**RÃ©ponse:**
```json
{
  "timestamp": "2026-05-28T14:35:00.000000",
  "total_results": 32,
  "success": {
    "count": 30,
    "rate_percent": 93.75
  },
  "failed": {
    "count": 2,
    "rate_percent": 6.25,
    "details": [
      {
        "result_id": "res-001",
        "task_id": "task-001",
        "agent_id": "a1b2c3d4-...",
        "error_message": "Command execution timeout",
        "created_at": "2026-05-28T14:30:00.000000"
      }
    ]
  },
  "avg_execution_time_ms": 245.5,
  "results_by_agent": {
    "a1b2c3d4-...": {
      "count": 27,
      "success": 25,
      "failed": 2
    }
  }
}
```

### Alertes du systÃ¨me

#### GET /api/monitoring/alerts

RÃ©cupÃ©rer les alertes dÃ©tectÃ©es automatiquement.

**Types d'alertes:**
- **agent_inactive**: Aucun beacon depuis 2+ heures (CRITICAL)
- **agent_slow**: Aucun beacon depuis 30+ minutes (WARNING)
- **agent_never_beaconed**: Agent crÃ©Ã© mais jamais connectÃ© (CRITICAL)
- **task_timeout**: TÃ¢che assignÃ©e au-delÃ  du timeout (WARNING)

**RÃ©ponse:**
```json
{
  "timestamp": "2026-05-28T14:35:00.000000",
  "overall_level": "warning",
  "critical_alerts": 1,
  "warning_alerts": 3,
  "alerts": [
    {
      "level": "critical",
      "type": "agent_inactive",
      "agent_id": "a1b2c3d4-...",
      "agent_name": "AUDIT-05",
      "message": "Agent inactive for 2.5 hours",
      "timestamp": "2026-05-28T14:35:00.000000"
    },
    {
      "level": "warning",
      "type": "agent_slow",
      "agent_id": "e5f6-7890-...",
      "agent_name": "AUDIT-08",
      "message": "Agent not responded for 45.0 minutes",
      "timestamp": "2026-05-28T14:35:00.000000"
    }
  ]
}
```

### Dashboard complet

#### GET /api/monitoring/dashboard

**âš ï¸ ATTENTION**: Endpoint lourd - combine tous les dashboards

RÃ©cupÃ©rer le dashboard complet (overview + agents + tasks + results + alerts).

```bash
curl http://localhost:8000/api/monitoring/dashboard
```

### Cas d'usage - Monitoring

**VÃ©rifier la santÃ© globale du systÃ¨me:**
```python
import requests

response = requests.get("http://localhost:8000/api/monitoring/overview")
overview = response.json()

print(f"Agents actifs: {overview['agents']['by_status']['active']}/{overview['agents']['total']}")
print(f"Taux de succÃ¨s: {overview['results']['by_status']['success']}/{overview['results']['total']}")
```

**DÃ©tecter les problÃ¨mes:**
```python
response = requests.get("http://localhost:8000/api/monitoring/alerts")
alerts = response.json()

if alerts["overall_level"] == "critical":
    for alert in alerts["alerts"]:
        if alert["level"] == "critical":
            print(f"âš ï¸ {alert['message']}")
```

**Analyser les performances:**
```python
response = requests.get("http://localhost:8000/api/monitoring/results")
results = response.json()

print(f"Temps d'exÃ©cution moyen: {results['avg_execution_time_ms']}ms")
print(f"Taux de succÃ¨s: {results['success']['rate_percent']}%")
```

---

## Application Web - Dashboard Vue.js

L'API est complÃ©tÃ©e par une **application web Vue.js** pour que l'administrateur systÃ¨me puisse visualiser et gÃ©rer le parc informatique sans accÃ©der directement Ã  la base de donnÃ©es.

### ðŸŽ¯ FonctionnalitÃ©s

- **Dashboard global**: Vue d'ensemble de la conformitÃ© du parc
- **Surveillance des agents**: Ã‰tat en temps rÃ©el de chaque machine
- **Alertes**: DÃ©tection automatique des problÃ¨mes (agents inactifs, tÃ¢ches en retard, etc.)
- **Lancement d'audits**: Bouton pour crÃ©er des tÃ¢ches audit par agent
- **Machines hors-ligne**: Tableau dÃ©diÃ© aux agents inaccessibles
- **Auto-rafraÃ®chissement**: Mise Ã  jour automatique toutes les 30 secondes

### ðŸ“‚ Fichiers

```
web/
â”œâ”€â”€ index.html          # Interface principale
â”œâ”€â”€ js/
â”‚   â”œâ”€â”€ api.js         # Client API (communication avec FastAPI)
â”‚   â””â”€â”€ app.js         # Application Vue.js
â”œâ”€â”€ css/
â”‚   â””â”€â”€ style.css      # Styles CSS
â””â”€â”€ README.md          # Documentation complÃ¨te
```

### ðŸš€ Lancement

#### Option 1: Avec Python (Simple)

```bash
cd web
python -m http.server 8080
```

AccÃ©dez Ã : **http://localhost:8080**

#### Option 2: Avec Node.js

```bash
npm install -g http-server
cd web
http-server -p 8080
```

#### Option 3: Ouvrir directement

Double-cliquez sur `web/index.html` (fonctionne avec le CDN Vue.js)

### âš™ï¸ Configuration API

Par dÃ©faut, l'application se connecte Ã  `http://localhost:8000/api`.

Pour modifier l'URL, Ã©ditez `web/js/api.js`:
```javascript
const API_BASE_URL = 'http://your-server:8000/api';
```

### ðŸ“Š Dashboard - Sections principales

#### 1. SantÃ© Globale
- Agents actifs/inactifs
- Taux de succÃ¨s global
- TÃ¢ches par statut

#### 2. Alertes
- Agents inactifs (2+ heures) - **CRITICAL**
- Agents lents (30+ minutes) - **WARNING**
- TÃ¢ches en retard

#### 3. Ã‰tat des Agents
Tableau avec statut, beacons, tÃ¢ches, taux de succÃ¨s pour chaque agent.

#### 4. Agents Hors Ligne
Liste spÃ©cifique des machines inaccessibles avec durÃ©e d'inactivitÃ©.

#### 5. Statistiques
- TÃ¢ches (en attente, assignÃ©es, complÃ©tÃ©es, Ã©chouÃ©es)
- Temps d'exÃ©cution moyen

### ðŸŽ¯ Lancer un Audit

1. Cliquez sur le bouton **"ðŸš€ Audit"** d'un agent
2. SÃ©lectionnez la commande:
   - `Get-AuditPolicy` - Politiques d'audit Windows
   - `Get-EventLog` - Logs d'Ã©vÃ©nements
   - `Get-LocalUser` - Utilisateurs locaux
   - `Get-Service` - Services
   - `Get-Process` - Processus
   - PersonnalisÃ©e - Entrez une commande PowerShell

3. SÃ©lectionnez la prioritÃ© (Normal / Haute / Critique)
4. Cliquez **"âœ“ Lancer l'Audit"**

L'audit est crÃ©Ã© et envoyÃ© Ã  l'agent pour exÃ©cution.

### ðŸ”‘ Points clÃ©s d'architecture

**SÃ©paration des responsabilitÃ©s:**
- âŒ L'agent PowerShell ne parle **JAMAIS** Ã  la BD directement (risque de sÃ©curitÃ©)
- âœ… L'agent communique **TOUJOURS** via l'API
- âœ… L'API valide, sÃ©curise et insÃ¨re les donnÃ©es

**Communication:**
```
PowerShell Agent  â†’  API REST  â†’  Base de DonnÃ©es
     (sÃ©curisÃ©e)      (validÃ©e)     (protÃ©gÃ©e)
```

### ðŸ“š Documentation Web

Pour plus de dÃ©tails sur l'application web, consultez [web/README.md](web/README.md).

---

## Prochaines Ã©tapes

1. âœ… **Base de donnÃ©es persistante**: IntÃ©grer MongoDB
2. âœ… **Logging amÃ©liorÃ©**: Ajouter logging structurÃ© (ex: Python logging)
3. âœ… **Rate limiting**: Limiter les requÃªtes par agent
4. âœ… **Historique**: Conserver l'historique des beacons
5. âœ… **Monitoring**: Dashboard pour surveiller les agents et tÃ¢ches
6. âœ… **Interface Web**: Dashboard Vue.js pour l'administrateur
7. **WebSocket**: Notifications en temps rÃ©el (push au lieu de polling)
8. **Chiffrement**: Chiffrer les rÃ©sultats sensibles

---

## Licence

Ã€ dÃ©finir selon votre projet.

