# Jadus Audit API - Python FastAPI

API REST pour gérer et coordonner les agents PowerShell d'audit de sécurité.

## Architecture

```
server_C2/
├── app/
│   ├── __init__.py
│   ├── models.py          # Modèles Pydantic (requêtes/réponses)
│   ├── database.py        # Gestion de la base de données
│   ├── auth.py            # Authentification des agents
│   ├── routes.py          # Endpoints (routes)
│   ├── logger.py          # Système de logging structuré
│   ├── rate_limiter.py    # Rate limiting par agent/endpoint
│   └── monitoring.py      # Monitoring et dashboards
├── web/                   # Application Vue.js (frontend)
│   ├── index.html         # Interface principale
│   ├── js/
│   │   ├── api.js        # Client API
│   │   └── app.js        # Application Vue
│   ├── css/
│   │   └── style.css     # Styles
│   └── README.md         # Documentation web
├── main.py                # Point d'entrée FastAPI
├── requirements.txt       # Dépendances Python
├── .env                   # Variables d'environnement
├── .gitignore
└── README.md             # Ce fichier
```

## Installation

### 1. Créer un environnement virtuel Python

```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Lancer le serveur

```bash
python main.py
# Ou directement avec uvicorn:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Le serveur démarre sur `http://localhost:8000`

### Documentation interactive

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### 1. **POST /api/enroll** - Enregistrement d'un agent

Première connexion de l'agent pour recevoir son ID unique et sa clé API.

**Requête:**
```json
{
  "agent_name": "AUDIT-AGENT-01",
  "os_version": "Windows 10 Enterprise",
  "hostname": "SERVER-01",
  "username": "SYSTEM"
}
```

**Réponse (200):**
```json
{
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "api_key": "f1e2d3c4-b5a6-7890-cdef-1234567890ab",
  "message": "Agent AUDIT-AGENT-01 enrolled successfully"
}
```

---

### 2. **POST /api/beacon** - Heartbeat + Récupération des tâches

L'agent envoie son état et reçoit les tâches en attente.

**Requête:**
```json
{
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "api_key": "f1e2d3c4-b5a6-7890-cdef-1234567890ab",
  "status": "online",
  "last_task_id": null,
  "uptime_seconds": 3600
}
```

**Réponse (200):**
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

### 3. **POST /api/results** - Envoi des résultats d'audit

L'agent envoie le compte-rendu d'une tâche complétée.

**Requête:**
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

**Réponse (200):**
```json
{
  "message": "Result for task task-001 acknowledged",
  "acknowledged": true
}
```

---

## Endpoints de gestion (pour les tests/debug)

### GET /api/agents
Lister tous les agents enregistrés.

### GET /api/tasks/{agent_id}
Lister les tâches d'un agent.

### POST /api/tasks/{agent_id}
Créer une nouvelle tâche pour un agent.

**Paramètres:**
- `command`: Commande à exécuter
- `parameters`: Paramètres optionnels
- `priority`: Priorité de la tâche (0 = normal)

### GET /api/results/{agent_id}
Récupérer tous les résultats d'un agent.

---

## Flux de fonctionnement

```
1. ENROLL (première connexion)
   Agent → POST /api/enroll → Reçoit agent_id + api_key

2. BEACON (heartbeat + récupération des tâches)
   Agent → POST /api/beacon (toutes les 30s) → Reçoit les tâches
   
3. EXECUTE (agent exécute les tâches)
   Agent exécute localement (PowerShell)
   
4. RESULTS (envoi des résultats)
   Agent → POST /api/results → Serveur enregistre le résultat
```

---

## Authentification

Chaque requête (sauf `/api/enroll`) doit incluire:
- `agent_id`: Identifiant unique de l'agent
- `api_key`: Clé API fournie lors de l'enregistrement

---

## Base de données

### Configuration Actuelle: MongoDB (Persistant)

L'API utilise **MongoDB** pour stocker les données de manière persistante.

**Avantages de MongoDB pour un EDR:**
- ✅ Schéma flexible (résultats d'audit avec structures variées)
- ✅ JSON natif (PowerShell retourne du JSON)
- ✅ Scalabilité (100+ agents sans problème)
- ✅ Index automatiques (performant)

**Fichiers:**
- [app/database_mongodb.py](app/database_mongodb.py) - Couche MongoDB
- [migrate_to_mongodb.py](migrate_to_mongodb.py) - Script de migration
- [MONGODB_SETUP.md](MONGODB_SETUP.md) - Guide installation MongoDB

**Installation rapide:**
```bash
# Avec Docker (recommandé)
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Puis installer les dépendances
pip install -r requirements.txt  # Contient pymongo

# Mettre à jour .env
DATABASE_MODE=mongodb
MONGODB_URL=mongodb://localhost:27017
```

📖 **Guide complet:** [MONGODB_SETUP.md](MONGODB_SETUP.md)

---

## Structure des modèles de données

### Agent
- `agent_id`: UUID unique
- `api_key`: Clé d'authentification
- `agent_name`: Nom de l'agent
- `os_version`: Version de l'OS
- `hostname`: Hostname du serveur
- `username`: Utilisateur connecté
- `status`: ACTIVE/INACTIVE/COMPROMISED
- `created_at`: Date d'enregistrement
- `last_beacon`: Dernier beacon reçu

### Task
- `task_id`: UUID unique
- `agent_id`: Agent destinataire
- `command`: Commande à exécuter
- `parameters`: Paramètres JSON
- `priority`: Priorité (0 = normal)
- `status`: PENDING/ASSIGNED/COMPLETED/FAILED
- `timeout_seconds`: Timeout d'exécution
- `created_at`, `assigned_at`, `completed_at`: Timestamps

### AuditResult
- `result_id`: UUID unique
- `task_id`: Tâche associée
- `agent_id`: Agent source
- `status`: "success" ou "failed"
- `result`: Données du résultat (JSON)
- `execution_time_ms`: Temps d'exécution
- `error_message`: Message d'erreur (si applicable)
- `created_at`: Timestamp

---

## Variables d'environnement

```env
HOST=0.0.0.0              # Interface d'écoute
PORT=8000                 # Port du serveur
ENV=development           # Mode (development/production)
ALLOWED_ORIGINS=...       # Domaines CORS autorisés
LOG_LEVEL=INFO            # Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# Rate Limiting
ENROLL_RATE_LIMIT=5       # Max 5 enrollements
ENROLL_WINDOW_SECONDS=3600  # Par heure

BEACON_RATE_LIMIT=100     # Max 100 beacons
BEACON_WINDOW_SECONDS=3600  # Par heure

RESULTS_RATE_LIMIT=50     # Max 50 soumissions de résultats
RESULTS_WINDOW_SECONDS=3600  # Par heure
```

---

## Rate Limiting

L'API implémente un système de **rate limiting par agent et par endpoint** pour prévenir les abus et les attaques par débordement.

### Fonctionnement

- **Sliding Window**: Les requêtes sont comptées dans une fenêtre de temps glissante
- **Par endpoint**: Limites différentes pour enroll, beacon, et results
- **Par agent**: Chaque agent a un compteur indépendant
- **Réponse 429**: Retournée si le limit est dépassé

### Limites par défaut

| Endpoint | Limite | Fenêtre |
|----------|--------|---------|
| `/api/enroll` | 5 requêtes | 1 heure |
| `/api/beacon` | 100 requêtes | 1 heure |
| `/api/results` | 50 requêtes | 1 heure |

### Réponse lors du dépassement

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

**Exemple de réponse:**
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

L'API enregistre automatiquement chaque **beacon** (connexion/heartbeat) d'un agent pour tracer son activité au fil du temps.

### Données enregistrées par beacon

- `beacon_id`: Identifiant unique du beacon
- `agent_id`: Agent source
- `beacon_status`: État signalé par l'agent (online, offline, etc.)
- `uptime_seconds`: Uptime de l'agent
- `tasks_count`: Nombre de tâches assignées
- `ip_address`: IP source (optionnel)
- `created_at`: Timestamp du beacon

### Endpoints d'historique

#### GET /api/beacon-history/{agent_id}

Récupérer les derniers beacons d'un agent.

**Paramètres:**
- `agent_id`: ID de l'agent
- `limit`: Nombre de beacons à retourner (défaut: 100, max: 1000)

**Exemple:**
```bash
curl http://localhost:8000/api/beacon-history/a1b2c3d4-... -G -d "limit=50"
```

**Réponse:**
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

Récupérer les statistiques globales de beacon pour un agent.

**Paramètres:**
- `agent_id`: ID de l'agent

**Réponse:**
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

**Tracer l'activité d'un agent:**
```python
import requests

agent_id = "a1b2c3d4-..."

# Récupérer les 10 derniers beacons
response = requests.get(f"http://localhost:8000/api/beacon-history/{agent_id}", 
                       params={"limit": 10})
beacons = response.json()["beacons"]

# Analyser la disponibilité
print(f"Dernière connexion: {beacons[0]['created_at']}")
print(f"Uptime moyen: {beacons[0]['uptime_seconds'] / 3600:.1f} heures")
```

**Détecter les agents inactifs:**
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

L'API fournit des **endpoints de monitoring et de dashboard** pour surveiller l'état global du système, les agents, tâches et résultats en temps réel.

### Vue d'ensemble du système

#### GET /api/monitoring/overview

Récupérer une vue d'ensemble des statistiques globales.

**Réponse:**
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

Récupérer le dashboard détaillé de tous les agents.

**Réponse:**
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

**Détection d'inactivité:**
- `is_inactive = true` si dernier beacon > 1 heure
- Utile pour identifier les agents en problème

### Dashboard des tâches

#### GET /api/monitoring/tasks

Récupérer le dashboard des tâches avec détection de problèmes.

**Réponse:**
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

**Détection des tâches en retard:**
- Tâches assignées depuis plus longtemps que leur timeout
- Identifie les blocages potentiels

### Dashboard des résultats

#### GET /api/monitoring/results

Récupérer le dashboard des résultats et taux de succès.

**Réponse:**
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

### Alertes du système

#### GET /api/monitoring/alerts

Récupérer les alertes détectées automatiquement.

**Types d'alertes:**
- **agent_inactive**: Aucun beacon depuis 2+ heures (CRITICAL)
- **agent_slow**: Aucun beacon depuis 30+ minutes (WARNING)
- **agent_never_beaconed**: Agent créé mais jamais connecté (CRITICAL)
- **task_timeout**: Tâche assignée au-delà du timeout (WARNING)

**Réponse:**
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

**⚠️ ATTENTION**: Endpoint lourd - combine tous les dashboards

Récupérer le dashboard complet (overview + agents + tasks + results + alerts).

```bash
curl http://localhost:8000/api/monitoring/dashboard
```

### Cas d'usage - Monitoring

**Vérifier la santé globale du système:**
```python
import requests

response = requests.get("http://localhost:8000/api/monitoring/overview")
overview = response.json()

print(f"Agents actifs: {overview['agents']['by_status']['active']}/{overview['agents']['total']}")
print(f"Taux de succès: {overview['results']['by_status']['success']}/{overview['results']['total']}")
```

**Détecter les problèmes:**
```python
response = requests.get("http://localhost:8000/api/monitoring/alerts")
alerts = response.json()

if alerts["overall_level"] == "critical":
    for alert in alerts["alerts"]:
        if alert["level"] == "critical":
            print(f"⚠️ {alert['message']}")
```

**Analyser les performances:**
```python
response = requests.get("http://localhost:8000/api/monitoring/results")
results = response.json()

print(f"Temps d'exécution moyen: {results['avg_execution_time_ms']}ms")
print(f"Taux de succès: {results['success']['rate_percent']}%")
```

---

## Application Web - Dashboard Vue.js

L'API est complétée par une **application web Vue.js** pour que l'administrateur système puisse visualiser et gérer le parc informatique sans accéder directement à la base de données.

### 🎯 Fonctionnalités

- **Dashboard global**: Vue d'ensemble de la conformité du parc
- **Surveillance des agents**: État en temps réel de chaque machine
- **Alertes**: Détection automatique des problèmes (agents inactifs, tâches en retard, etc.)
- **Lancement d'audits**: Bouton pour créer des tâches audit par agent
- **Machines hors-ligne**: Tableau dédié aux agents inaccessibles
- **Auto-rafraîchissement**: Mise à jour automatique toutes les 30 secondes

### 📂 Fichiers

```
web/
├── index.html          # Interface principale
├── js/
│   ├── api.js         # Client API (communication avec FastAPI)
│   └── app.js         # Application Vue.js
├── css/
│   └── style.css      # Styles CSS
└── README.md          # Documentation complète
```

### 🚀 Lancement

#### Option 1: Avec Python (Simple)

```bash
cd web
python -m http.server 8080
```

Accédez à: **http://localhost:8080**

#### Option 2: Avec Node.js

```bash
npm install -g http-server
cd web
http-server -p 8080
```

#### Option 3: Ouvrir directement

Double-cliquez sur `web/index.html` (fonctionne avec le CDN Vue.js)

### ⚙️ Configuration API

Par défaut, l'application se connecte à `http://localhost:8000/api`.

Pour modifier l'URL, éditez `web/js/api.js`:
```javascript
const API_BASE_URL = 'http://your-server:8000/api';
```

### 📊 Dashboard - Sections principales

#### 1. Santé Globale
- Agents actifs/inactifs
- Taux de succès global
- Tâches par statut

#### 2. Alertes
- Agents inactifs (2+ heures) - **CRITICAL**
- Agents lents (30+ minutes) - **WARNING**
- Tâches en retard

#### 3. État des Agents
Tableau avec statut, beacons, tâches, taux de succès pour chaque agent.

#### 4. Agents Hors Ligne
Liste spécifique des machines inaccessibles avec durée d'inactivité.

#### 5. Statistiques
- Tâches (en attente, assignées, complétées, échouées)
- Temps d'exécution moyen

### 🎯 Lancer un Audit

1. Cliquez sur le bouton **"🚀 Audit"** d'un agent
2. Sélectionnez la commande:
   - `Get-AuditPolicy` - Politiques d'audit Windows
   - `Get-EventLog` - Logs d'événements
   - `Get-LocalUser` - Utilisateurs locaux
   - `Get-Service` - Services
   - `Get-Process` - Processus
   - Personnalisée - Entrez une commande PowerShell

3. Sélectionnez la priorité (Normal / Haute / Critique)
4. Cliquez **"✓ Lancer l'Audit"**

L'audit est créé et envoyé à l'agent pour exécution.

### 🔑 Points clés d'architecture

**Séparation des responsabilités:**
- ❌ L'agent PowerShell ne parle **JAMAIS** à la BD directement (risque de sécurité)
- ✅ L'agent communique **TOUJOURS** via l'API
- ✅ L'API valide, sécurise et insère les données

**Communication:**
```
PowerShell Agent  →  API REST  →  Base de Données
     (sécurisée)      (validée)     (protégée)
```

### 📚 Documentation Web

Pour plus de détails sur l'application web, consultez [web/README.md](web/README.md).

---

## Prochaines étapes

1. ✅ **Base de données persistante**: Intégrer MongoDB
2. ✅ **Logging amélioré**: Ajouter logging structuré (ex: Python logging)
3. ✅ **Rate limiting**: Limiter les requêtes par agent
4. ✅ **Historique**: Conserver l'historique des beacons
5. ✅ **Monitoring**: Dashboard pour surveiller les agents et tâches
6. ✅ **Interface Web**: Dashboard Vue.js pour l'administrateur
7. **WebSocket**: Notifications en temps réel (push au lieu de polling)
8. **Chiffrement**: Chiffrer les résultats sensibles

---

## Licence

À définir selon votre projet.
