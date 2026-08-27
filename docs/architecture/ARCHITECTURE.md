# 🏗️ Architecture Technique - Jadus Audit

## Vue d'ensemble

### Trois Couches Principales

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                 ADMINISTRATEUR (Frontend)                   â”‚
â”‚                                                             â”‚
â”‚  Vue.js Dashboard (web/)                                   â”‚
â”‚  - Surveillance en temps rÃ©el                              â”‚
â”‚  - Lancement d'audits                                      â”‚
â”‚  - Gestion du parc informatique                            â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
                       â”‚ HTTP REST / JSON
                       â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                   API REST (Backend)                        â”‚
â”‚                                                             â”‚
â”‚  FastAPI (Python) - app/routes.py                          â”‚
â”‚  - Authentification (agent_id + api_key)                   â”‚
â”‚  - Rate limiting (5/h enroll, 100/h beacon, 50/h results)  â”‚
â”‚  - Validation des donnÃ©es (Pydantic)                       â”‚
â”‚  - Monitoring (alertes, dashboards)                        â”‚
â”‚  - Logging structurÃ© (JSON)                                â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                       â”‚
                       â”‚ MongoDB / En-mÃ©moire (failover)
                       â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚               BASE DE DONNÃ‰ES (Stockage)                    â”‚
â”‚                                                             â”‚
â”‚  Production: MongoDB (PERSISTANT sur disque)               â”‚
â”‚  DÃ©veloppement: Dictionnaires en mÃ©moire (fallback)        â”‚
â”‚  SÃ©lection: DATABASE_MODE env var (mongodb/memory)         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Agents PowerShell

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  PowerShell Agent   â”‚
â”‚  (Local Machine)    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
           â”‚
           â”‚ POST /api/enroll (agent_id, api_key)
           â”‚ POST /api/beacon (heartbeat)
           â”‚ POST /api/results (audit results)
           â”‚
           â†“
    âœ… JAMAIS d'accÃ¨s direct Ã  la BD âœ…
           â†“
        API REST (SÃ©curisÃ©e)
```

## Composants du Backend

### 1. **app/models.py** - ModÃ¨les de DonnÃ©es

DÃ©finit la structure de toutes les requÃªtes/rÃ©ponses via Pydantic:

```python
# RequÃªtes
- EnrollRequest: agent_name, os_version, hostname, username
- BeaconRequest: agent_id, api_key, status, uptime_seconds
- AuditResultRequest: task_id, status, result, execution_time_ms

# RÃ©ponses
- EnrollResponse: agent_id, api_key, message
- BeaconResponse: tasks[], next_beacon_interval

# EntitÃ©s
- Agent: Informations de l'agent enregistrÃ©
- Task: TÃ¢che Ã  exÃ©cuter
- AuditResult: RÃ©sultat d'une tÃ¢che
- BeaconHistory: Historique des heartbeats
```

**Avantage**: Validation automatique, documentation auto-gÃ©nÃ©rÃ©e, sÃ©curitÃ©.

### 2. **app/database.py** - Couche DonnÃ©es (DÃ©veloppement/Fallback)

Abstraction de la base de donnÃ©es en mÃ©moire pour dÃ©veloppement et failover:

```python
# In-memory (dÃ©veloppement + failover si MongoDB indisponible)
agents = {}          # agent_id â†’ Agent
tasks = {}           # task_id â†’ Task
results = {}         # result_id â†’ AuditResult
beacon_history = {}  # agent_id â†’ [BeaconHistory]

# Les donnÃ©es sont perdues au redÃ©marrage
# Parfait pour les tests et dÃ©veloppement
# Activation: DATABASE_MODE=memory
```

### 2b. **app/database_mongodb.py** - Couche DonnÃ©es (Production)

ImplÃ©mentation MongoDB pour la production avec **PERSISTANCE DISQUE**:

```python
# MongoDB (production - PERSISTANT)
db.agents              # Collection agents (index unique sur agent_id)
db.tasks              # Collection tasks avec status tracking
db.audit_results      # Collection audit_results (rÃ©sultats audits)
db.beacon_history     # Collection beacon_history (historique heartbeats)

# AVANTAGES:
âœ… Persistance disque: Les donnÃ©es survivent aux redÃ©marrages
âœ… Index automatiques: Recherches trÃ¨s rapides
âœ… SchÃ©ma flexible: RÃ©sultats JSON variÃ©s (Get-Service, Get-AuditPolicy, etc.)
âœ… Transactions ACID: IntÃ©gritÃ© des donnÃ©es garantie
âœ… ScalabilitÃ©: PrÃªt pour les gros volumes de donnÃ©es

# Configuration: DATABASE_MODE=mongodb (dÃ©faut en production)
```

**Setup MongoDB:** [MONGODB_SETUP.md](../MONGODB_SETUP.md)

### 2c. **app/db.py** - Gestionnaire d'Instance Singleton

Pattern singleton pour gÃ©rer la sÃ©lection runtime:

```python
# SÃ©lection automatique au startup (main.py)
if DATABASE_MODE == "mongodb":
    db_instance = MongoDatabase()  # â† Production PERSISTANT
else:
    db_instance = Database()       # â† DÃ©veloppement (en mÃ©moire)

# Toutes les routes utilisent get_db()
db = get_db()
agents = db.list_agents()  # Fonctionne sur les deux
```

**Avantage:** Interface identique â†’ facile de basculer entre les deux

### 3. **app/routes.py** - Endpoints API

12 endpoints organisÃ©s par fonction:

#### Agents (6 endpoints)
```
POST   /api/enroll                          # Inscription
GET    /api/agents                          # Lister tous
GET    /api/agents/{agent_id}               # DÃ©tails d'un agent
GET    /api/beacon-history/{agent_id}       # Historique beacons
GET    /api/beacon-stats/{agent_id}         # Stats beacons
```

#### TÃ¢ches (2 endpoints)
```
GET    /api/tasks/{agent_id}                # TÃ¢ches en attente
POST   /api/tasks/{agent_id}                # CrÃ©er une tÃ¢che
```

#### RÃ©sultats (2 endpoints)
```
POST   /api/results                         # Soumettre un rÃ©sultat
GET    /api/results/{agent_id}              # RÃ©cupÃ©rer rÃ©sultats
```

#### Monitoring (6 endpoints)
```
GET    /api/monitoring/overview             # Vue d'ensemble
GET    /api/monitoring/agents               # Dashboard agents
GET    /api/monitoring/tasks                # Dashboard tÃ¢ches
GET    /api/monitoring/results              # Dashboard rÃ©sultats
GET    /api/monitoring/alerts               # Alertes systÃ¨me
GET    /api/monitoring/dashboard            # Tout combinÃ©
```

#### Utilitaires
```
GET    /api/rate-limit/stats/{agent_id}/{endpoint}
```

### 4. **app/auth.py** - Authentification

```python
def verify_agent_credentials(agent_id: str, api_key: str) -> bool:
    """VÃ©rifier que l'agent_id + api_key sont valides"""
    agent = db.get_agent(agent_id)
    return agent and agent.api_key == api_key
```

**Points clÃ©s**:
- Pas de JWT complexe (pas nÃ©cessaire pour les agents)
- UUID + clÃ© API simple mais sÃ©curisÃ©
- Logging de toutes les tentatives

### 5. **app/logger.py** - Logging StructurÃ©

```python
# Dual Output
- Console: Lisible pour les admins (couleurs)
- Fichier: JSON pour l'archivage et analyse

# Formato JSON
{
  "timestamp": "2026-05-28T14:35:00Z",
  "level": "INFO",
  "logger": "Jadus",
  "message": "Audit launched",
  "agent_id": "a1b2c3d4-...",
  "task_id": "task-001"
}

# Rotation
- Taille max: 10 MB par fichier
- Archivage: 10 fichiers de backup
```

### 6. **app/rate_limiter.py** - Protection Anti-Abus

```python
# Sliding Window Algorithm
- Enroll: 5 requÃªtes/heure par agent
- Beacon: 100 requÃªtes/heure par agent
- Results: 50 requÃªtes/heure par agent

# Retour
- Allowed: (True, requests_made, requests_remaining)
- Denied: (False, requests_made, requests_remaining) + HTTP 429
```

### 7. **app/monitoring.py** - Analytics

```python
def get_system_overview():
    """Stats globales du systÃ¨me"""
    - Total agents, tÃ¢ches, rÃ©sultats
    - RÃ©partition par statut
    - Temps moyen d'exÃ©cution

def get_agents_dashboard():
    """Stats par agent"""
    - Statut (active/inactive)
    - Beacon stats (total, premiÃ¨re, derniÃ¨re)
    - TÃ¢ches assignÃ©es/complÃ©tÃ©es
    - Taux de succÃ¨s

def get_alerts():
    """DÃ©tection de problÃ¨mes"""
    - Agents inactifs 2h+ â†’ CRITICAL
    - Agents lents 30m+ â†’ WARNING
    - Agents jamais connectÃ©s â†’ CRITICAL
    - TÃ¢ches en retard â†’ WARNING
```

### 8. **app/encryption.py** - Chiffrement AES-256-GCM

Chiffre les rÃ©sultats d'audits sensibles avant stockage en base de donnÃ©es:

```python
# Approche Hybrid (SÃ©curitÃ© + Recherche)
class Encryptor:
    def encrypt(plaintext: str) -> Tuple[str, str]
        # AES-256-GCM chiffrement authentifiÃ©
        # Retourne: (encrypted_b64, nonce_hex)
    
    def decrypt(encrypted_b64: str) -> str
        # DÃ©chiffrement avec vÃ©rification d'authenticitÃ©
        # DÃ©tecte le tampering
    
    @staticmethod
    def hash_result(plaintext: str) -> str
        # SHA-256 pour recherche sans dÃ©chiffrement
    
    @staticmethod
    def generate_preview(plaintext: str) -> str
        # "Output: 2500 bytes, 45 lines" (non-sensible)
```

**StratÃ©gie de SÃ©curitÃ©:**

```
Avant stockage en BD:
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Plaintext       â”‚ (ex: Get-Service output)
â”‚ 2500 bytes      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
    â”Œâ”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚                      â”‚                 â”‚              â”‚
    â–¼                      â–¼                 â–¼              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Encrypt     â”‚   â”‚ Hash (SHA256)â”‚  â”‚ Preview      â”‚  â”‚ Original â”‚
â”‚ AES-256-GCM â”‚   â”‚ (for search) â”‚  â”‚ (safe to UI) â”‚  â”‚ (memory) â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
      â”‚                 â”‚                   â”‚              â”‚
      â–¼                 â–¼                   â–¼              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    Base de DonnÃ©es                             â”‚
â”‚  result_encrypted: "aBc123XyZ...==" (chiffrÃ©)                 â”‚
â”‚  result_hash: "a3f9jadus..." (pour recherche exact-match)         â”‚
â”‚  result_preview: "Output: 2500 bytes, 45 lines" (safe)       â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
      â”‚                                    â”‚
      â”œâ”€â”€â”€ AccÃ¨s: Personne sauf l'admin  â”‚
      â”‚    (Protected by database auth)   â”‚
      â”‚                                    â”‚
      â””â”€â”€â”€ AccÃ¨s: Audit trail, monitoring â”€â–º (Public preview only)
```

**CaractÃ©ristiques de SÃ©curitÃ©:**

```
âœ… AES-256-GCM: Chiffrement authentifiÃ© (dÃ©tecte tampering)
âœ… Nonce alÃ©atoire: Chaque encryption gÃ©nÃ¨re un rÃ©sultat diffÃ©rent
âœ… PBKDF2: DÃ©rivation de clÃ© avec 480k itÃ©rations (OWASP standard)
âœ… Hash pour recherche: Permet "trouver" sans dÃ©chiffrer
âœ… Preview non-sensible: L'UI voit structure mais pas les donnÃ©es
âœ… Rotation clÃ©: Via ENCRYPTION_KEY env var
```

**Architecture d'IntÃ©gration:**

```
1. Stockage (store_result):
   plaintext â†’ Encrypt â†’ result_encrypted (BD)
            â†’ Hash    â†’ result_hash (BD)
            â†’ Preview â†’ result_preview (BD)
            â†’ Keep    â†’ result (mÃ©moire seulement)

2. RÃ©cupÃ©ration (get_result):
   result_encrypted (BD) â†’ Decrypt â†’ plaintext (retournÃ©)
   
3. Audit/Monitoring:
   result_hash â†’ Peut chercher par hash (exact match)
   result_preview â†’ Affiche dans l'UI (safe)

4. Configuration:
   ENCRYPTION_KEY env var (minimum 32 chars)
   Exemple: export ENCRYPTION_KEY='your-secure-master-key-here'
```

**Couverture de Tests:**

```
- 29 tests de chiffrement (test/test_encryption.py)
- Round-trip encryption/decryption âœ…
- DÃ©tection de tampering âœ…
- Mauvaise clÃ© â†’ Erreur âœ…
- Hash consistency âœ…
- Preview generation âœ…
- PowerShell output encryption âœ…
- JSON result encryption âœ…
- Database integration âœ…
```

### 9. **Documentation OpenAPI** - API Documentation Auto-gÃ©nÃ©rÃ©e

FastAPI gÃ©nÃ¨re automatiquement la documentation OpenAPI complÃ¨te:

```
GET /api/docs            â†’ Swagger UI (interactive)
GET /api/redoc           â†’ ReDoc (beautiful documentation)
GET /api/openapi.json    â†’ OpenAPI 3.0 schema (machine-readable)
```

**Configuration:**

```python
# main.py
app = FastAPI(
    title="Jadus Audit API",
    description="...",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=TAGS_METADATA,
    servers=SERVERS,
)
```

**CaractÃ©ristiques:**

```
âœ… Tags: Organisation par catÃ©gorie (Agents, Tasks, Results, Monitoring)
âœ… Descriptions: DÃ©tails complets de chaque endpoint
âœ… Examples: Exemples de requÃªtes/rÃ©ponses
âœ… Schemas: Validation automatique des donnÃ©es
âœ… Rate Limiting: Documentation des limites
âœ… Error Codes: Tous les codes HTTP documentÃ©s
```

**Documentation Statique:**

```
- API_DOCUMENTATION.md: Guide complet avec exemples
- openapi.json: SchÃ©ma machine-readable
- app/openapi_config.py: Configuration centralisÃ©e
- generate_openapi.py: Script pour gÃ©nÃ©rer le schÃ©ma
```

**Usages:**

```bash
# GÃ©nÃ©rer le schÃ©ma
python generate_openapi.py

# Tester les endpoints
curl http://localhost:8000/api/docs

# Importer dans Postman
1. Ouvrir Postman
2. File â†’ Import
3. Coller: http://localhost:8000/api/openapi.json
```

**Couverture OpenAPI:**

```
Endpoints documentÃ©s: 19
  - 6 agents (enroll, list, details, history, stats)
  - 2 tasks (list, create)
  - 3 results (submit, list, detail)
  - 6 monitoring (overview, agents, tasks, results, alerts, dashboard)
  - 2 utility (health, admin)

Schemas: 10 composants
  - Requests: EnrollRequest, BeaconRequest, TaskCreateRequest, etc.
  - Responses: EnrollResponse, BeaconResponse, AuditResultResponse, etc.
  - Models: Agent, Task, AuditResult, BeaconHistory

Tags: 5 categories
  - Agents: Agent management
  - Tasks: Task management
  - Results: Result submission and retrieval
  - Monitoring: System analytics
  - Health: Status endpoints
```

### 10. **app/admin_auth.py** - JWT Admin Authentication

Fournit l'authentification admin avec tokens JWT pour l'accÃ¨s aux endpoints de monitoring:

```python
class JWTError(Exception):
    """Base exception for JWT errors"""

def create_jwt_token(username: str) -> str:
    """GÃ©nÃ©rer un token JWT pour admin"""

def verify_jwt_token(token: str) -> dict:
    """VÃ©rifier et dÃ©coder un token JWT"""

def verify_admin_credentials(username: str, password: str) -> bool:
    """VÃ©rifier les identifiants admin"""

def extract_token_from_header(auth_header: str) -> Optional[str]:
    """Extraire le token du header Authorization"""
```

**Configuration:**

```bash
# Variables d'environnement
ADMIN_SECRET_KEY=your-secure-key-min-32-chars    # ClÃ© de signature JWT
ADMIN_USERNAME=admin                              # Nom d'utilisateur
ADMIN_PASSWORD=changeme                           # Mot de passe
JWT_EXPIRATION_HOURS=24                           # DurÃ©e de validitÃ© du token
```

**Fonctionnement:**

```
1. Admin se connecte
   POST /api/admin/login
   {
     "username": "admin",
     "password": "changeme"
   }
   
   â†“
   
   RÃ©ponse:
   {
     "access_token": "eyJhbGciOiJIUzI1NiIs...",
     "token_type": "bearer",
     "expires_in": 86400,
     "message": "Login successful"
   }

2. Admin utilise le token pour accÃ©der Ã  monitoring
   GET /api/monitoring/overview
   Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
   
   â†“
   
   [Endpoint vÃ©rifie le JWT]
   [Token valide â†’ Retourne les donnÃ©es]
   [Token invalide/expirÃ© â†’ HTTP 401]

3. Endpoints protÃ©gÃ©s par JWT:
   - GET /api/monitoring/overview
   - GET /api/monitoring/agents
   - GET /api/monitoring/tasks
   - GET /api/monitoring/results
   - GET /api/monitoring/alerts
   - GET /api/monitoring/dashboard
```

**CaractÃ©ristiques de SÃ©curitÃ©:**

```
âœ… JWT HS256: HMAC avec SHA-256 pour signature
âœ… Token Expiration: Expires aprÃ¨s 24h (configurable)
âœ… Secret Validation: Minimum 32 caractÃ¨res
âœ… Credential Validation: VÃ©rification des identifiants
âœ… Header Extraction: Support du format "Bearer <token>"
âœ… Error Handling: Distinction token expirÃ© vs invalide
âœ… Logging: Toutes les tentatives enregistrÃ©es
```

**Exemple d'Utilisation (PowerShell):**

```powershell
# 1. Connexion
$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/admin/login" `
  -Method Post `
  -Headers @{"Content-Type" = "application/json"} `
  -Body (@{username = "admin"; password = "changeme"} | ConvertTo-Json)

$token = $loginResponse.access_token
$expires_in = $loginResponse.expires_in
Write-Host "Token obtained, valid for $($expires_in / 3600) hours"

# 2. Utilisation du token
$headers = @{
  "Authorization" = "Bearer $token"
  "Content-Type" = "application/json"
}

$overview = Invoke-RestMethod `
  -Uri "http://localhost:8000/api/monitoring/overview" `
  -Headers $headers

$overview | ConvertTo-Json
```

**Couverture de Tests:**

```
- 29 tests de JWT (test/test_admin_auth.py)
- Token generation âœ…
- Token verification âœ…
- Token expiration âœ…
- Credential validation âœ…
- Header extraction âœ…
- Error handling âœ…
- Integration flows âœ…
```

**SÃ©curitÃ© en Production:**

```
âš ï¸  Recommandations:
1. DÃ©finir ADMIN_SECRET_KEY robuste (min 32 chars, random)
2. Utiliser HTTPS (TLS/SSL) pour toutes les requÃªtes
3. ImplÃ©menter MFA (Multi-factor authentication)
4. Rotation rÃ©guliÃ¨re des tokens
5. Audit logging de toutes les opÃ©rations admin
6. Limiter les tentatives de connexion (brute force protection)
7. IP whitelisting pour les connexions admin
```

### 11. **app/admin_auth.py** (Phase 4) - Bcrypt Password Hashing

Enhanced admin authentication with bcrypt password hashing for secure credential storage:

```python
def hash_password(password: str) -> str:
    """GÃ©nÃ©rer un hash bcrypt sÃ©curisÃ© (12 rounds)"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """VÃ©rifier un mot de passe contre son hash bcrypt"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def verify_admin_credentials(username: str, password: str) -> bool:
    """VÃ©rifier les identifiants avec support bcrypt"""
    if ADMIN_PASSWORD_HASH:
        return verify_password(password, ADMIN_PASSWORD_HASH)
    else:
        return password == ADMIN_PASSWORD_PLAINTEXT  # Fallback pour dÃ©veloppement
```

**CaractÃ©ristiques:**

```
âœ… Bcrypt: 12 rounds salt (industry standard)
âœ… SÃ©curitÃ©: Passwords jamais stockÃ©s en plaintext
âœ… Fallback: Mode dÃ©veloppement avec plaintext si ADMIN_PASSWORD_HASH non dÃ©fini
âœ… Production: DÃ©finir ADMIN_PASSWORD_HASH en env var avec hash bcrypt
âœ… Test coverage: 6 tests (hash creation, verification, edge cases)
```

**Configuration (Production):**

```bash
# GÃ©nÃ©rer un hash bcrypt
python -c "from app.admin_auth import hash_password; print(hash_password('secure_password'))"

# Sortie: $2b$12$aBcDeF123...xyz123==

# Puis dÃ©finir en env:
export ADMIN_PASSWORD_HASH='$2b$12$aBcDeF123...xyz123=='
```

### 12. **app/routes.py** (Phase 4) - Rate Limiting on Admin Login

Enhanced `/api/admin/login` endpoint with rate limiting to prevent brute force attacks:

```python
@router.post("/api/admin/login", tags=["Admin"])
async def admin_login(request: AdminLoginRequest):
    """
    Admin login with rate limiting protection
    
    Rate Limit: 5 attempts per hour per IP address
    
    Returns:
    - 200: Login successful, access_token provided
    - 401: Invalid credentials
    - 429: Too many login attempts (rate limit exceeded)
    """
    # Extract IP from request (handles proxies via x-forwarded-for)
    ip_address = extract_client_ip(request)
    
    # Rate limiting: 5 attempts/hour per IP
    allowed, _, _ = rate_limiter.is_allowed(
        entity_id=ip_address,
        endpoint="/admin/login",
        limit=5,                    # ADMIN_LOGIN_LIMIT
        window_seconds=3600         # ADMIN_LOGIN_WINDOW_SECONDS
    )
    
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many login attempts")
    
    # Verify credentials with bcrypt if configured
    if verify_admin_credentials(request.username, request.password):
        token = create_jwt_token(request.username)
        return AdminLoginResponse(access_token=token, ...)
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

**CaractÃ©ristiques:**

```
âœ… Rate Limiting: 5 attempts/hour par adresse IP
âœ… Proxy Support: Extrait IP de x-forwarded-for header
âœ… HTTP 429: RÃ©ponse standard pour rate limit exceeded
âœ… Sliding Window: Algorithme avec fenÃªtre glissante
âœ… Configuration: ADMIN_LOGIN_LIMIT et ADMIN_LOGIN_WINDOW_SECONDS env vars
âœ… Test coverage: Tests de rate limiting
```

### 13. **main.py** (Phase 4) - Payload Size Validation Middleware

Middleware to prevent Denial-of-Service attacks via large payloads:

```python
class PayloadSizeValidationMiddleware(BaseHTTPMiddleware):
    """Valider la taille du payload pour prÃ©venir les attaques DoS"""
    
    async def dispatch(self, request: Request, call_next):
        # VÃ©rifier Content-Length header
        content_length = request.headers.get("content-length")
        
        if content_length and int(content_length) > MAX_PAYLOAD_SIZE:
            logger.warning(
                f"Payload too large from {request.client.host}: "
                f"{content_length} bytes (limit: {MAX_PAYLOAD_SIZE})"
            )
            return JSONResponse(
                status_code=413,
                content={"detail": "Payload too large"}
            )
        
        return await call_next(request)
```

**CaractÃ©ristiques:**

```
âœ… Default: 10 MB limit (MAX_PAYLOAD_SIZE env var)
âœ… HTTP 413: RÃ©ponse standard pour payload trop gros
âœ… Logging: Enregistrement des tentatives suspectes
âœ… Middleware: PlacÃ© avant CORS dans la stack
âœ… Performance: VÃ©rification du header avant traitement
âœ… Configuration: MAX_PAYLOAD_SIZE env var (bytes)
```

### 14. **app/logger.py** (Phase 4) - Secrets Filtering

SecretsFilter class to prevent sensitive data exposure in logs:

```python
class SecretsFilter(logging.Filter):
    """Masquer les donnÃ©es sensibles dans les logs"""
    
    PATTERNS = [
        # JWT tokens (eyJ...)
        (r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[REDACTED_JWT]'),
        # API keys
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9_-]+["\']?', 'api_key=[REDACTED]'),
        # Bearer tokens
        (r'Bearer\s+[A-Za-z0-9_.-]+', 'Bearer [REDACTED]'),
        # Passwords
        (r'password["\']?\s*[:=]\s*["\']?[^"\'\s,}]+["\']?', 'password=[REDACTED]'),
        # Database URLs
        (r'mongodb://[^:]+:[^@]+@', 'mongodb://[REDACTED]:[REDACTED]@'),
        # AWS keys
        (r'aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9/+=]+["\']?', 
         'aws_secret_access_key=[REDACTED]'),
        # Encryption keys
        (r'ADMIN_PASSWORD["\']?\s*[:=]\s*["\']?[^"\'\s,}]+["\']?', 'ADMIN_PASSWORD=[REDACTED]'),
        (r'ADMIN_SECRET_KEY["\']?\s*[:=]\s*["\']?[^"\'\s,}]+["\']?', 'ADMIN_SECRET_KEY=[REDACTED]'),
        (r'ENCRYPTION_KEY["\']?\s*[:=]\s*["\']?[^"\'\s,}]+["\']?', 'ENCRYPTION_KEY=[REDACTED]'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log records"""
        for pattern, replacement in self.PATTERNS:
            record.msg = re.sub(pattern, replacement, str(record.msg), flags=re.IGNORECASE)
        return True
```

**CaractÃ©ristiques:**

```
âœ… 9 Regex Patterns: JWT, API keys, passwords, DB URLs, AWS keys, etc.
âœ… Case-Insensitive: DÃ©tecte les variantes (Password, PASSWORD, pwd, etc.)
âœ… Applied Globally: Tous les handlers (console + fichiers)
âœ… Unicode Safe: PrÃ©serve les textes non-sensibles
âœ… No Exceptions: Continue le logging mÃªme si filtrage Ã©choue
âœ… Test coverage: 8 tests de masquage
```

**RÃ©sultat Before/After:**

```
âŒ BEFORE (log sensible):
[INFO] Login attempt: username=admin, password=secretPass123
[INFO] Database connected: mongodb://admin:password123@host:27017

âœ… AFTER (log sÃ©curisÃ©):
[INFO] Login attempt: username=admin, password=[REDACTED]
[INFO] Database connected: mongodb://[REDACTED]:[REDACTED]@host:27017
```

## Composants du Frontend

### 1. **index.html** - Interface

```html
- Header: Titre + sous-titre
- Container principal:
  - Section 1: SantÃ© globale (stat boxes)
  - Section 2: Alertes
  - Section 3: Ã‰tat des agents (tableau)
  - Section 4: Agents offline
  - Section 5: RÃ©sumÃ© tÃ¢ches
- Modal: Lancer un audit
```

### 2. **js/api.js** - Client API

```javascript
class JadusApiClient {
  static async getSystemOverview()
  static async getAgentsDashboard()
  static async getTasksDashboard()
  static async getResultsDashboard()
  static async getAlerts()
  static async createTask(agentId, command, priority)
  // ... plus 10 autres mÃ©thodes
}

const formatters = {
  formatDate()
  formatDuration()
  formatPercent()
  getStatusClass()
  getAlertLevelClass()
}
```

**Avantage**: SÃ©paration claire API â†” UI

### 3. **js/app.js** - Application Vue.js

```javascript
const app = createApp({
  data() {
    return {
      overview, agents, tasks, alerts,  // donnÃ©es
      loading, apiError,                 // Ã©tat
      showAuditModal, selectedAgent,    // modal
    };
  },
  
  methods: {
    loadDashboardData()    // Charger les donnÃ©es
    launchAudit()          // Ouvrir modal
    submitAudit()          // Soumettre audit
    startAutoRefresh()     // 30s auto-refresh
  },
  
  computed: {
    successRate()          // CalculÃ© dynamiquement
    inactiveAgents()       // FiltrÃ© dynamiquement
  }
});
```

**FonctionnalitÃ©s Vue.js**:
- RÃ©activitÃ©: Mise Ã  jour auto de l'UI
- Two-way binding: v-model pour les formulaires
- Conditionnels: v-if, v-for
- Ã‰vÃ©nements: @click, @submit
- Templates: interpolation {{ }}, directives

### 4. **css/style.css** - Styling

```css
- Variables CSS: couleurs, espacements
- Mobile-first responsive design
- Animations et transitions
- ThÃ¨me professionnel:
  - Bleu (#0066cc) pour actions
  - Vert (#28a745) pour succÃ¨s
  - Rouge (#dc3545) pour erreurs
  - Gris (#6c757d) pour muted
```

## Flux de DonnÃ©es

### Enregistrement Agent

```
PowerShell Agent
    â†“ POST /api/enroll
        {agent_name, os_version, hostname, username}
            â†“ [API validation]
                â†“ [DB create agent]
                    â†“ [Generate UUID + API key]
                        â†“ [Log event]
                            â†“ Response
Admin Dashboard â† Agents list updated (30s)
```

### ExÃ©cution Audit

```
Admin clicks "ðŸš€ Audit"
    â†“ Modal: Select command + priority
        â†“ POST /api/tasks/{agent_id}
            {command, priority}
                â†“ [Rate limit check]
                    â†“ [Auth check]
                        â†“ [DB create task]
                            â†“ [Log audit event]
                                â†“ Response: task_id
                                    â†“ "âœ“ Audit launched!"
PowerShell Agent (beacon)
    â†“ POST /api/beacon
        {agent_id, api_key}
            â†“ [Auth check]
                â†“ [Rate limit check]
                    â†“ [Record beacon]
                        â†“ Response
                            â†“ GET pending tasks
                                â†“ Execute task locally
                                    â†“ POST /api/results
                                        {task_id, result, execution_time}
                                            â†“ [Store in DB]
Admin Dashboard â† Sees completed task
```

## SÃ©curitÃ©

### Niveau 1: Rate Limiting

```
POST /api/beacon (100 requÃªtes/heure)
POST /api/enroll (5 requÃªtes/heure)
POST /api/results (50 requÃªtes/heure)
POST /api/admin/login (5 requÃªtes/heure par IP) â† NOUVEAU Phase 4

â†“ Si dÃ©passement
HTTP 429 Too Many Requests
```

### Niveau 2: Authentification

```
Agents (legacy):
- agent_id valid?
- api_key matching?
â†’ Sinon: HTTP 401 Unauthorized

Admin (Phase 4 - JWT + Bcrypt):
- Credentials validÃ©s avec bcrypt
- JWT token gÃ©nÃ©rÃ© (HS256)
- Token requiert pour monitoring endpoints
- Expiration 24h (configurable)
â†’ Sinon: HTTP 401 Unauthorized
```

### Niveau 3: Validation

```
Pydantic vÃ©rifie:
- Types corrects?
- Champs obligatoires?
- Valeurs dans les ranges?
â†’ Sinon: HTTP 422 Unprocessable Entity
```

### Niveau 4: Payload Size Validation (Phase 4)

```
Tous les requests vÃ©rifient Content-Length:
- Limit par dÃ©faut: 10 MB (MAX_PAYLOAD_SIZE env var)
- Protection contre les attaques DoS
â†’ Si dÃ©passement: HTTP 413 Payload Too Large
```

### Niveau 5: SÃ©paration des ResponsabilitÃ©s

```
âŒ JAMAIS: PowerShell Agent â†’ Database (faille majeure!)
âœ… TOUJOURS: PowerShell Agent â†’ API â†’ Database
```

### Niveau 6: Secrets Filtering in Logs (Phase 4)

```
Toutes les donnÃ©es sensibles masquÃ©es:
- JWT tokens â†’ [REDACTED_JWT]
- Passwords â†’ [REDACTED]
- API keys â†’ [REDACTED]
- Database URLs â†’ [REDACTED]
- Encryption keys â†’ [REDACTED]

AppliquÃ© Ã :
âœ… Console output
âœ… Log files (JSON)
âœ… Error traces
```

### Niveau 7: Password Security (Phase 4)

```
Admin credentials:
âœ… Bcrypt hashing with 12-round salt
âœ… Never stored in plaintext
âœ… Passwords verified with bcrypt.checkpw()
âœ… Development fallback for ease-of-use
```

### Niveau 8: Audit Logging

```
Tous les Ã©vÃ©nements loggÃ©s:
- Enregistrement d'agent
- Tentatives d'auth (succÃ¨s/Ã©checs)
- CrÃ©ation de tÃ¢ches
- Soumission de rÃ©sultats
- Erreurs et exceptions
- Admin login attempts (IP, timestamp)

â†’ Fichiers JSON pour compliance
```

## Performances

### Optimisations Actuelles

```
- MongoDB Index: AccÃ¨s O(1) sur indexed fields
- Query Optimization: Dashboard prÃ©-aggrÃ©gÃ©
- Auto-refresh 30s: Pas de polling agressif
- JSON compact: RÃ©ductions de taille
- Connection pooling: RÃ©utilisation des connexions
```

### Futures AmÃ©liorations

```
- Caching: Redis pour stats
- WebSocket: Push au lieu de polling
- Compression: gzip pour rÃ©ponses
- CDN: Assets statiques (Vue.js, CSS)
- Sharding MongoDB: Si 1000+ agents
- Read replicas: Pour haute disponibilitÃ©
```

## DÃ©ploiement

### DÃ©veloppement (Mode MÃ©moire)

```bash
Terminal 1: python main.py (API sur :8000)
Terminal 2: cd web && python -m http.server 8080
â†’ Utilise la mÃ©moire (donnÃ©es perdues au redÃ©marrage)
```

### Production (Avec MongoDB)

**Infrastructure:**
```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Load Balancer   â”‚
â”‚ (Nginx)         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
    â”Œâ”€â”€â”€â”€â”´â”€â”€â”€â”€â”
    â”‚          â”‚
â”Œâ”€â”€â”€â–¼â”€â”€â”  â”Œâ”€â”€â”€â–¼â”€â”€â”
â”‚API 1 â”‚  â”‚API 2 â”‚  (Gunicorn + Uvicorn)
â”‚:8000 â”‚  â”‚:8001 â”‚  (Workers multiples)
â””â”€â”€â”€â”¬â”€â”€â”˜  â””â”€â”€â”€â”¬â”€â”€â”˜
    â”‚         â”‚
    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”˜
         â”‚
    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚ MongoDB Replica Set     â”‚
    â”‚ - Primary               â”‚
    â”‚ - Secondary 1           â”‚
    â”‚ - Secondary 2           â”‚
    â”‚ (Haute disponibilitÃ©)   â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

**API Backend:**
```bash
# Avec Gunicorn (workers multiples)
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# Ou avec Docker
docker run -d \
  -p 8000:8000 \
  -e MONGODB_URL=mongodb://mongodb-host:27017 \
  -e DATABASE_MODE=mongodb \
  my-jadus-api:latest
```

**Frontend:**
```bash
# Build Vue.js (production)
# npm run build (aprÃ¨s npm install)
# Servir via Nginx/CDN

# Ou avec Docker
docker run -d \
  -p 80:80 \
  -v /path/to/web:/usr/share/nginx/html \
  nginx:latest
```

**MongoDB:**
```bash
# Docker
docker run -d \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=secure_pass \
  mongo:latest

# Ou managed service (Atlas, Compass, etc.)
# MONGODB_URL=mongodb+srv://admin:pass@cluster.mongodb.net/jadus_server
```

**SSL/TLS:**
```bash
# Nginx avec Let's Encrypt
# certbot certonly --standalone -d your-domain.com
# Puis configurer nginx pour HTTPS
```

**Monitoring:**
- Prometheus + Grafana pour les mÃ©triques
- ELK stack (Elasticsearch, Logstash, Kibana) pour les logs
- MongoDB Compass pour la DB
- Alertes Slack/Email pour les incidents

## Checklist d'IntÃ©gration

### âœ… Phase 1-3: Core Features

- [x] API REST 12 endpoints
- [x] Authentification agent
- [x] Rate limiting
- [x] Logging structurÃ©
- [x] Beacon history
- [x] Monitoring/dashboards
- [x] Dashboard web Vue.js
- [x] Lancement d'audits
- [x] Chiffrement rÃ©sultats (AES-256-GCM)
- [x] OpenAPI documentation (19 endpoints)
- [x] JWT Admin authentication

### âœ… Phase 4: Security Hardening - Tier 1 (COMPLETED)

- [x] Bcrypt password hashing for admin credentials
- [x] Rate limiting on /admin/login (5 attempts/hour per IP)
- [x] Payload size validation middleware (10 MB default)
- [x] Secrets filtering in logs (9 regex patterns)
- [x] 18 security tests (100% pass rate)

### ðŸŸ¡ Phase 5: Security Hardening - Tier 2 (PENDING)

- [ ] Detailed audit logging (who, what, when, where for sensitive ops)
- [ ] CSRF protection (frontend token validation)
- [ ] HTTP security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- [ ] XSS prevention (HTML escaping in Vue.js templates)

### ðŸŸ¡ Phase 6: Security Hardening - Tier 3 (PENDING)

- [ ] SQL injection prevention (parameterized queries)
- [ ] CORS policy refinement (restrict origins)
- [ ] Session management improvements (secure cookies)
- [ ] Encryption key rotation mechanism

### ðŸŸ¡ Future Improvements

- [ ] Test load (1000+ agents)
- [ ] CI/CD pipeline
- [ ] MFA (Multi-factor authentication)
- [ ] IP whitelisting for admin
- [ ] Caching: Redis for stats
- [ ] WebSocket: Push instead of polling
- [ ] Compression: gzip for responses
- [ ] CDN: Static assets (Vue.js, CSS)
- [ ] Sharding MongoDB: If 1000+ agents
- [ ] Read replicas: High availability

---

**Architecture complÃ¨te et extensible âœ…**
**Phase 4 Security Hardening Complete âœ… (4/4 Tier 1 items)**

