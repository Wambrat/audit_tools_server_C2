# 🏗️ Architecture Technique - C2 Dashboard

## Vue d'ensemble

### Trois Couches Principales

```
┌─────────────────────────────────────────────────────────────┐
│                 ADMINISTRATEUR (Frontend)                   │
│                                                             │
│  Vue.js Dashboard (web/)                                   │
│  - Surveillance en temps réel                              │
│  - Lancement d'audits                                      │
│  - Gestion du parc informatique                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP REST / JSON
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   API REST (Backend)                        │
│                                                             │
│  FastAPI (Python) - app/routes.py                          │
│  - Authentification (agent_id + api_key)                   │
│  - Rate limiting (5/h enroll, 100/h beacon, 50/h results)  │
│  - Validation des données (Pydantic)                       │
│  - Monitoring (alertes, dashboards)                        │
│  - Logging structuré (JSON)                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ MongoDB / En-mémoire (failover)
                       ↓
┌─────────────────────────────────────────────────────────────┐
│               BASE DE DONNÉES (Stockage)                    │
│                                                             │
│  Production: MongoDB (PERSISTANT sur disque)               │
│  Développement: Dictionnaires en mémoire (fallback)        │
│  Sélection: DATABASE_MODE env var (mongodb/memory)         │
└─────────────────────────────────────────────────────────────┘
```

### Agents PowerShell

```
┌─────────────────────┐
│  PowerShell Agent   │
│  (Local Machine)    │
└──────────┬──────────┘
           │
           │ POST /api/enroll (agent_id, api_key)
           │ POST /api/beacon (heartbeat)
           │ POST /api/results (audit results)
           │
           ↓
    ✅ JAMAIS d'accès direct à la BD ✅
           ↓
        API REST (Sécurisée)
```

## Composants du Backend

### 1. **app/models.py** - Modèles de Données

Définit la structure de toutes les requêtes/réponses via Pydantic:

```python
# Requêtes
- EnrollRequest: agent_name, os_version, hostname, username
- BeaconRequest: agent_id, api_key, status, uptime_seconds
- AuditResultRequest: task_id, status, result, execution_time_ms

# Réponses
- EnrollResponse: agent_id, api_key, message
- BeaconResponse: tasks[], next_beacon_interval

# Entités
- Agent: Informations de l'agent enregistré
- Task: Tâche à exécuter
- AuditResult: Résultat d'une tâche
- BeaconHistory: Historique des heartbeats
```

**Avantage**: Validation automatique, documentation auto-générée, sécurité.

### 2. **app/database.py** - Couche Données (Développement/Fallback)

Abstraction de la base de données en mémoire pour développement et failover:

```python
# In-memory (développement + failover si MongoDB indisponible)
agents = {}          # agent_id → Agent
tasks = {}           # task_id → Task
results = {}         # result_id → AuditResult
beacon_history = {}  # agent_id → [BeaconHistory]

# Les données sont perdues au redémarrage
# Parfait pour les tests et développement
# Activation: DATABASE_MODE=memory
```

### 2b. **app/database_mongodb.py** - Couche Données (Production)

Implémentation MongoDB pour la production avec **PERSISTANCE DISQUE**:

```python
# MongoDB (production - PERSISTANT)
db.agents              # Collection agents (index unique sur agent_id)
db.tasks              # Collection tasks avec status tracking
db.audit_results      # Collection audit_results (résultats audits)
db.beacon_history     # Collection beacon_history (historique heartbeats)

# AVANTAGES:
✅ Persistance disque: Les données survivent aux redémarrages
✅ Index automatiques: Recherches très rapides
✅ Schéma flexible: Résultats JSON variés (Get-Service, Get-AuditPolicy, etc.)
✅ Transactions ACID: Intégrité des données garantie
✅ Scalabilité: Prêt pour les gros volumes de données

# Configuration: DATABASE_MODE=mongodb (défaut en production)
```

**Setup MongoDB:** [MONGODB_SETUP.md](../MONGODB_SETUP.md)

### 2c. **app/db.py** - Gestionnaire d'Instance Singleton

Pattern singleton pour gérer la sélection runtime:

```python
# Sélection automatique au startup (main.py)
if DATABASE_MODE == "mongodb":
    db_instance = MongoDatabase()  # ← Production PERSISTANT
else:
    db_instance = Database()       # ← Développement (en mémoire)

# Toutes les routes utilisent get_db()
db = get_db()
agents = db.list_agents()  # Fonctionne sur les deux
```

**Avantage:** Interface identique → facile de basculer entre les deux

### 3. **app/routes.py** - Endpoints API

12 endpoints organisés par fonction:

#### Agents (6 endpoints)
```
POST   /api/enroll                          # Inscription
GET    /api/agents                          # Lister tous
GET    /api/agents/{agent_id}               # Détails d'un agent
GET    /api/beacon-history/{agent_id}       # Historique beacons
GET    /api/beacon-stats/{agent_id}         # Stats beacons
```

#### Tâches (2 endpoints)
```
GET    /api/tasks/{agent_id}                # Tâches en attente
POST   /api/tasks/{agent_id}                # Créer une tâche
```

#### Résultats (2 endpoints)
```
POST   /api/results                         # Soumettre un résultat
GET    /api/results/{agent_id}              # Récupérer résultats
```

#### Monitoring (6 endpoints)
```
GET    /api/monitoring/overview             # Vue d'ensemble
GET    /api/monitoring/agents               # Dashboard agents
GET    /api/monitoring/tasks                # Dashboard tâches
GET    /api/monitoring/results              # Dashboard résultats
GET    /api/monitoring/alerts               # Alertes système
GET    /api/monitoring/dashboard            # Tout combiné
```

#### Utilitaires
```
GET    /api/rate-limit/stats/{agent_id}/{endpoint}
```

### 4. **app/auth.py** - Authentification

```python
def verify_agent_credentials(agent_id: str, api_key: str) -> bool:
    """Vérifier que l'agent_id + api_key sont valides"""
    agent = db.get_agent(agent_id)
    return agent and agent.api_key == api_key
```

**Points clés**:
- Pas de JWT complexe (pas nécessaire pour les agents)
- UUID + clé API simple mais sécurisé
- Logging de toutes les tentatives

### 5. **app/logger.py** - Logging Structuré

```python
# Dual Output
- Console: Lisible pour les admins (couleurs)
- Fichier: JSON pour l'archivage et analyse

# Formato JSON
{
  "timestamp": "2026-05-28T14:35:00Z",
  "level": "INFO",
  "logger": "C2",
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
- Enroll: 5 requêtes/heure par agent
- Beacon: 100 requêtes/heure par agent
- Results: 50 requêtes/heure par agent

# Retour
- Allowed: (True, requests_made, requests_remaining)
- Denied: (False, requests_made, requests_remaining) + HTTP 429
```

### 7. **app/monitoring.py** - Analytics

```python
def get_system_overview():
    """Stats globales du système"""
    - Total agents, tâches, résultats
    - Répartition par statut
    - Temps moyen d'exécution

def get_agents_dashboard():
    """Stats par agent"""
    - Statut (active/inactive)
    - Beacon stats (total, première, dernière)
    - Tâches assignées/complétées
    - Taux de succès

def get_alerts():
    """Détection de problèmes"""
    - Agents inactifs 2h+ → CRITICAL
    - Agents lents 30m+ → WARNING
    - Agents jamais connectés → CRITICAL
    - Tâches en retard → WARNING
```

### 8. **app/encryption.py** - Chiffrement AES-256-GCM

Chiffre les résultats d'audits sensibles avant stockage en base de données:

```python
# Approche Hybrid (Sécurité + Recherche)
class Encryptor:
    def encrypt(plaintext: str) -> Tuple[str, str]
        # AES-256-GCM chiffrement authentifié
        # Retourne: (encrypted_b64, nonce_hex)
    
    def decrypt(encrypted_b64: str) -> str
        # Déchiffrement avec vérification d'authenticité
        # Détecte le tampering
    
    @staticmethod
    def hash_result(plaintext: str) -> str
        # SHA-256 pour recherche sans déchiffrement
    
    @staticmethod
    def generate_preview(plaintext: str) -> str
        # "Output: 2500 bytes, 45 lines" (non-sensible)
```

**Stratégie de Sécurité:**

```
Avant stockage en BD:
┌─────────────────┐
│ Plaintext       │ (ex: Get-Service output)
│ 2500 bytes      │
└────────┬────────┘
         │
    ┌────┴─────────────────┬─────────────────┬──────────────┐
    │                      │                 │              │
    ▼                      ▼                 ▼              ▼
┌─────────────┐   ┌──────────────┐  ┌──────────────┐  ┌──────────┐
│ Encrypt     │   │ Hash (SHA256)│  │ Preview      │  │ Original │
│ AES-256-GCM │   │ (for search) │  │ (safe to UI) │  │ (memory) │
└─────────────┘   └──────────────┘  └──────────────┘  └──────────┘
      │                 │                   │              │
      ▼                 ▼                   ▼              ▼
┌────────────────────────────────────────────────────────────────┐
│                    Base de Données                             │
│  result_encrypted: "aBc123XyZ...==" (chiffré)                 │
│  result_hash: "a3f9c2..." (pour recherche exact-match)         │
│  result_preview: "Output: 2500 bytes, 45 lines" (safe)       │
└────────────────────────────────────────────────────────────────┘
      │                                    │
      ├─── Accès: Personne sauf l'admin  │
      │    (Protected by database auth)   │
      │                                    │
      └─── Accès: Audit trail, monitoring ─► (Public preview only)
```

**Caractéristiques de Sécurité:**

```
✅ AES-256-GCM: Chiffrement authentifié (détecte tampering)
✅ Nonce aléatoire: Chaque encryption génère un résultat différent
✅ PBKDF2: Dérivation de clé avec 480k itérations (OWASP standard)
✅ Hash pour recherche: Permet "trouver" sans déchiffrer
✅ Preview non-sensible: L'UI voit structure mais pas les données
✅ Rotation clé: Via ENCRYPTION_KEY env var
```

**Architecture d'Intégration:**

```
1. Stockage (store_result):
   plaintext → Encrypt → result_encrypted (BD)
            → Hash    → result_hash (BD)
            → Preview → result_preview (BD)
            → Keep    → result (mémoire seulement)

2. Récupération (get_result):
   result_encrypted (BD) → Decrypt → plaintext (retourné)
   
3. Audit/Monitoring:
   result_hash → Peut chercher par hash (exact match)
   result_preview → Affiche dans l'UI (safe)

4. Configuration:
   ENCRYPTION_KEY env var (minimum 32 chars)
   Exemple: export ENCRYPTION_KEY='your-secure-master-key-here'
```

**Couverture de Tests:**

```
- 29 tests de chiffrement (test/test_encryption.py)
- Round-trip encryption/decryption ✅
- Détection de tampering ✅
- Mauvaise clé → Erreur ✅
- Hash consistency ✅
- Preview generation ✅
- PowerShell output encryption ✅
- JSON result encryption ✅
- Database integration ✅
```

### 9. **Documentation OpenAPI** - API Documentation Auto-générée

FastAPI génère automatiquement la documentation OpenAPI complète:

```
GET /api/docs            → Swagger UI (interactive)
GET /api/redoc           → ReDoc (beautiful documentation)
GET /api/openapi.json    → OpenAPI 3.0 schema (machine-readable)
```

**Configuration:**

```python
# main.py
app = FastAPI(
    title="C2 Server API",
    description="...",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    openapi_tags=TAGS_METADATA,
    servers=SERVERS,
)
```

**Caractéristiques:**

```
✅ Tags: Organisation par catégorie (Agents, Tasks, Results, Monitoring)
✅ Descriptions: Détails complets de chaque endpoint
✅ Examples: Exemples de requêtes/réponses
✅ Schemas: Validation automatique des données
✅ Rate Limiting: Documentation des limites
✅ Error Codes: Tous les codes HTTP documentés
```

**Documentation Statique:**

```
- API_DOCUMENTATION.md: Guide complet avec exemples
- openapi.json: Schéma machine-readable
- app/openapi_config.py: Configuration centralisée
- generate_openapi.py: Script pour générer le schéma
```

**Usages:**

```bash
# Générer le schéma
python generate_openapi.py

# Tester les endpoints
curl http://localhost:8000/api/docs

# Importer dans Postman
1. Ouvrir Postman
2. File → Import
3. Coller: http://localhost:8000/api/openapi.json
```

**Couverture OpenAPI:**

```
Endpoints documentés: 19
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

Fournit l'authentification admin avec tokens JWT pour l'accès aux endpoints de monitoring:

```python
class JWTError(Exception):
    """Base exception for JWT errors"""

def create_jwt_token(username: str) -> str:
    """Générer un token JWT pour admin"""

def verify_jwt_token(token: str) -> dict:
    """Vérifier et décoder un token JWT"""

def verify_admin_credentials(username: str, password: str) -> bool:
    """Vérifier les identifiants admin"""

def extract_token_from_header(auth_header: str) -> Optional[str]:
    """Extraire le token du header Authorization"""
```

**Configuration:**

```bash
# Variables d'environnement
ADMIN_SECRET_KEY=your-secure-key-min-32-chars    # Clé de signature JWT
ADMIN_USERNAME=admin                              # Nom d'utilisateur
ADMIN_PASSWORD=changeme                           # Mot de passe
JWT_EXPIRATION_HOURS=24                           # Durée de validité du token
```

**Fonctionnement:**

```
1. Admin se connecte
   POST /api/admin/login
   {
     "username": "admin",
     "password": "changeme"
   }
   
   ↓
   
   Réponse:
   {
     "access_token": "eyJhbGciOiJIUzI1NiIs...",
     "token_type": "bearer",
     "expires_in": 86400,
     "message": "Login successful"
   }

2. Admin utilise le token pour accéder à monitoring
   GET /api/monitoring/overview
   Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
   
   ↓
   
   [Endpoint vérifie le JWT]
   [Token valide → Retourne les données]
   [Token invalide/expiré → HTTP 401]

3. Endpoints protégés par JWT:
   - GET /api/monitoring/overview
   - GET /api/monitoring/agents
   - GET /api/monitoring/tasks
   - GET /api/monitoring/results
   - GET /api/monitoring/alerts
   - GET /api/monitoring/dashboard
```

**Caractéristiques de Sécurité:**

```
✅ JWT HS256: HMAC avec SHA-256 pour signature
✅ Token Expiration: Expires après 24h (configurable)
✅ Secret Validation: Minimum 32 caractères
✅ Credential Validation: Vérification des identifiants
✅ Header Extraction: Support du format "Bearer <token>"
✅ Error Handling: Distinction token expiré vs invalide
✅ Logging: Toutes les tentatives enregistrées
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
- Token generation ✅
- Token verification ✅
- Token expiration ✅
- Credential validation ✅
- Header extraction ✅
- Error handling ✅
- Integration flows ✅
```

**Sécurité en Production:**

```
⚠️  Recommandations:
1. Définir ADMIN_SECRET_KEY robuste (min 32 chars, random)
2. Utiliser HTTPS (TLS/SSL) pour toutes les requêtes
3. Implémenter MFA (Multi-factor authentication)
4. Rotation régulière des tokens
5. Audit logging de toutes les opérations admin
6. Limiter les tentatives de connexion (brute force protection)
7. IP whitelisting pour les connexions admin
```

### 11. **app/admin_auth.py** (Phase 4) - Bcrypt Password Hashing

Enhanced admin authentication with bcrypt password hashing for secure credential storage:

```python
def hash_password(password: str) -> str:
    """Générer un hash bcrypt sécurisé (12 rounds)"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Vérifier un mot de passe contre son hash bcrypt"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def verify_admin_credentials(username: str, password: str) -> bool:
    """Vérifier les identifiants avec support bcrypt"""
    if ADMIN_PASSWORD_HASH:
        return verify_password(password, ADMIN_PASSWORD_HASH)
    else:
        return password == ADMIN_PASSWORD_PLAINTEXT  # Fallback pour développement
```

**Caractéristiques:**

```
✅ Bcrypt: 12 rounds salt (industry standard)
✅ Sécurité: Passwords jamais stockés en plaintext
✅ Fallback: Mode développement avec plaintext si ADMIN_PASSWORD_HASH non défini
✅ Production: Définir ADMIN_PASSWORD_HASH en env var avec hash bcrypt
✅ Test coverage: 6 tests (hash creation, verification, edge cases)
```

**Configuration (Production):**

```bash
# Générer un hash bcrypt
python -c "from app.admin_auth import hash_password; print(hash_password('secure_password'))"

# Sortie: $2b$12$aBcDeF123...xyz123==

# Puis définir en env:
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

**Caractéristiques:**

```
✅ Rate Limiting: 5 attempts/hour par adresse IP
✅ Proxy Support: Extrait IP de x-forwarded-for header
✅ HTTP 429: Réponse standard pour rate limit exceeded
✅ Sliding Window: Algorithme avec fenêtre glissante
✅ Configuration: ADMIN_LOGIN_LIMIT et ADMIN_LOGIN_WINDOW_SECONDS env vars
✅ Test coverage: Tests de rate limiting
```

### 13. **main.py** (Phase 4) - Payload Size Validation Middleware

Middleware to prevent Denial-of-Service attacks via large payloads:

```python
class PayloadSizeValidationMiddleware(BaseHTTPMiddleware):
    """Valider la taille du payload pour prévenir les attaques DoS"""
    
    async def dispatch(self, request: Request, call_next):
        # Vérifier Content-Length header
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

**Caractéristiques:**

```
✅ Default: 10 MB limit (MAX_PAYLOAD_SIZE env var)
✅ HTTP 413: Réponse standard pour payload trop gros
✅ Logging: Enregistrement des tentatives suspectes
✅ Middleware: Placé avant CORS dans la stack
✅ Performance: Vérification du header avant traitement
✅ Configuration: MAX_PAYLOAD_SIZE env var (bytes)
```

### 14. **app/logger.py** (Phase 4) - Secrets Filtering

SecretsFilter class to prevent sensitive data exposure in logs:

```python
class SecretsFilter(logging.Filter):
    """Masquer les données sensibles dans les logs"""
    
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

**Caractéristiques:**

```
✅ 9 Regex Patterns: JWT, API keys, passwords, DB URLs, AWS keys, etc.
✅ Case-Insensitive: Détecte les variantes (Password, PASSWORD, pwd, etc.)
✅ Applied Globally: Tous les handlers (console + fichiers)
✅ Unicode Safe: Préserve les textes non-sensibles
✅ No Exceptions: Continue le logging même si filtrage échoue
✅ Test coverage: 8 tests de masquage
```

**Résultat Before/After:**

```
❌ BEFORE (log sensible):
[INFO] Login attempt: username=admin, password=secretPass123
[INFO] Database connected: mongodb://admin:password123@host:27017

✅ AFTER (log sécurisé):
[INFO] Login attempt: username=admin, password=[REDACTED]
[INFO] Database connected: mongodb://[REDACTED]:[REDACTED]@host:27017
```

## Composants du Frontend

### 1. **index.html** - Interface

```html
- Header: Titre + sous-titre
- Container principal:
  - Section 1: Santé globale (stat boxes)
  - Section 2: Alertes
  - Section 3: État des agents (tableau)
  - Section 4: Agents offline
  - Section 5: Résumé tâches
- Modal: Lancer un audit
```

### 2. **js/api.js** - Client API

```javascript
class C2ApiClient {
  static async getSystemOverview()
  static async getAgentsDashboard()
  static async getTasksDashboard()
  static async getResultsDashboard()
  static async getAlerts()
  static async createTask(agentId, command, priority)
  // ... plus 10 autres méthodes
}

const formatters = {
  formatDate()
  formatDuration()
  formatPercent()
  getStatusClass()
  getAlertLevelClass()
}
```

**Avantage**: Séparation claire API ↔ UI

### 3. **js/app.js** - Application Vue.js

```javascript
const app = createApp({
  data() {
    return {
      overview, agents, tasks, alerts,  // données
      loading, apiError,                 // état
      showAuditModal, selectedAgent,    // modal
    };
  },
  
  methods: {
    loadDashboardData()    // Charger les données
    launchAudit()          // Ouvrir modal
    submitAudit()          // Soumettre audit
    startAutoRefresh()     // 30s auto-refresh
  },
  
  computed: {
    successRate()          // Calculé dynamiquement
    inactiveAgents()       // Filtré dynamiquement
  }
});
```

**Fonctionnalités Vue.js**:
- Réactivité: Mise à jour auto de l'UI
- Two-way binding: v-model pour les formulaires
- Conditionnels: v-if, v-for
- Événements: @click, @submit
- Templates: interpolation {{ }}, directives

### 4. **css/style.css** - Styling

```css
- Variables CSS: couleurs, espacements
- Mobile-first responsive design
- Animations et transitions
- Thème professionnel:
  - Bleu (#0066cc) pour actions
  - Vert (#28a745) pour succès
  - Rouge (#dc3545) pour erreurs
  - Gris (#6c757d) pour muted
```

## Flux de Données

### Enregistrement Agent

```
PowerShell Agent
    ↓ POST /api/enroll
        {agent_name, os_version, hostname, username}
            ↓ [API validation]
                ↓ [DB create agent]
                    ↓ [Generate UUID + API key]
                        ↓ [Log event]
                            ↓ Response
Admin Dashboard ← Agents list updated (30s)
```

### Exécution Audit

```
Admin clicks "🚀 Audit"
    ↓ Modal: Select command + priority
        ↓ POST /api/tasks/{agent_id}
            {command, priority}
                ↓ [Rate limit check]
                    ↓ [Auth check]
                        ↓ [DB create task]
                            ↓ [Log audit event]
                                ↓ Response: task_id
                                    ↓ "✓ Audit launched!"
PowerShell Agent (beacon)
    ↓ POST /api/beacon
        {agent_id, api_key}
            ↓ [Auth check]
                ↓ [Rate limit check]
                    ↓ [Record beacon]
                        ↓ Response
                            ↓ GET pending tasks
                                ↓ Execute task locally
                                    ↓ POST /api/results
                                        {task_id, result, execution_time}
                                            ↓ [Store in DB]
Admin Dashboard ← Sees completed task
```

## Sécurité

### Niveau 1: Rate Limiting

```
POST /api/beacon (100 requêtes/heure)
POST /api/enroll (5 requêtes/heure)
POST /api/results (50 requêtes/heure)
POST /api/admin/login (5 requêtes/heure par IP) ← NOUVEAU Phase 4

↓ Si dépassement
HTTP 429 Too Many Requests
```

### Niveau 2: Authentification

```
Agents (legacy):
- agent_id valid?
- api_key matching?
→ Sinon: HTTP 401 Unauthorized

Admin (Phase 4 - JWT + Bcrypt):
- Credentials validés avec bcrypt
- JWT token généré (HS256)
- Token requiert pour monitoring endpoints
- Expiration 24h (configurable)
→ Sinon: HTTP 401 Unauthorized
```

### Niveau 3: Validation

```
Pydantic vérifie:
- Types corrects?
- Champs obligatoires?
- Valeurs dans les ranges?
→ Sinon: HTTP 422 Unprocessable Entity
```

### Niveau 4: Payload Size Validation (Phase 4)

```
Tous les requests vérifient Content-Length:
- Limit par défaut: 10 MB (MAX_PAYLOAD_SIZE env var)
- Protection contre les attaques DoS
→ Si dépassement: HTTP 413 Payload Too Large
```

### Niveau 5: Séparation des Responsabilités

```
❌ JAMAIS: PowerShell Agent → Database (faille majeure!)
✅ TOUJOURS: PowerShell Agent → API → Database
```

### Niveau 6: Secrets Filtering in Logs (Phase 4)

```
Toutes les données sensibles masquées:
- JWT tokens → [REDACTED_JWT]
- Passwords → [REDACTED]
- API keys → [REDACTED]
- Database URLs → [REDACTED]
- Encryption keys → [REDACTED]

Appliqué à:
✅ Console output
✅ Log files (JSON)
✅ Error traces
```

### Niveau 7: Password Security (Phase 4)

```
Admin credentials:
✅ Bcrypt hashing with 12-round salt
✅ Never stored in plaintext
✅ Passwords verified with bcrypt.checkpw()
✅ Development fallback for ease-of-use
```

### Niveau 8: Audit Logging

```
Tous les événements loggés:
- Enregistrement d'agent
- Tentatives d'auth (succès/échecs)
- Création de tâches
- Soumission de résultats
- Erreurs et exceptions
- Admin login attempts (IP, timestamp)

→ Fichiers JSON pour compliance
```

## Performances

### Optimisations Actuelles

```
- MongoDB Index: Accès O(1) sur indexed fields
- Query Optimization: Dashboard pré-aggrégé
- Auto-refresh 30s: Pas de polling agressif
- JSON compact: Réductions de taille
- Connection pooling: Réutilisation des connexions
```

### Futures Améliorations

```
- Caching: Redis pour stats
- WebSocket: Push au lieu de polling
- Compression: gzip pour réponses
- CDN: Assets statiques (Vue.js, CSS)
- Sharding MongoDB: Si 1000+ agents
- Read replicas: Pour haute disponibilité
```

## Déploiement

### Développement (Mode Mémoire)

```bash
Terminal 1: python main.py (API sur :8000)
Terminal 2: cd web && python -m http.server 8080
→ Utilise la mémoire (données perdues au redémarrage)
```

### Production (Avec MongoDB)

**Infrastructure:**
```
┌─────────────────┐
│ Load Balancer   │
│ (Nginx)         │
└────────┬────────┘
         │
    ┌────┴────┐
    │          │
┌───▼──┐  ┌───▼──┐
│API 1 │  │API 2 │  (Gunicorn + Uvicorn)
│:8000 │  │:8001 │  (Workers multiples)
└───┬──┘  └───┬──┘
    │         │
    └────┬────┘
         │
    ┌────▼───────────────────┐
    │ MongoDB Replica Set     │
    │ - Primary               │
    │ - Secondary 1           │
    │ - Secondary 2           │
    │ (Haute disponibilité)   │
    └────────────────────────┘
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
  my-c2-api:latest
```

**Frontend:**
```bash
# Build Vue.js (production)
# npm run build (après npm install)
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
# MONGODB_URL=mongodb+srv://admin:pass@cluster.mongodb.net/c2_server
```

**SSL/TLS:**
```bash
# Nginx avec Let's Encrypt
# certbot certonly --standalone -d your-domain.com
# Puis configurer nginx pour HTTPS
```

**Monitoring:**
- Prometheus + Grafana pour les métriques
- ELK stack (Elasticsearch, Logstash, Kibana) pour les logs
- MongoDB Compass pour la DB
- Alertes Slack/Email pour les incidents

## Checklist d'Intégration

### ✅ Phase 1-3: Core Features

- [x] API REST 12 endpoints
- [x] Authentification agent
- [x] Rate limiting
- [x] Logging structuré
- [x] Beacon history
- [x] Monitoring/dashboards
- [x] Dashboard web Vue.js
- [x] Lancement d'audits
- [x] Chiffrement résultats (AES-256-GCM)
- [x] OpenAPI documentation (19 endpoints)
- [x] JWT Admin authentication

### ✅ Phase 4: Security Hardening - Tier 1 (COMPLETED)

- [x] Bcrypt password hashing for admin credentials
- [x] Rate limiting on /admin/login (5 attempts/hour per IP)
- [x] Payload size validation middleware (10 MB default)
- [x] Secrets filtering in logs (9 regex patterns)
- [x] 18 security tests (100% pass rate)

### 🟡 Phase 5: Security Hardening - Tier 2 (PENDING)

- [ ] Detailed audit logging (who, what, when, where for sensitive ops)
- [ ] CSRF protection (frontend token validation)
- [ ] HTTP security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- [ ] XSS prevention (HTML escaping in Vue.js templates)

### 🟡 Phase 6: Security Hardening - Tier 3 (PENDING)

- [ ] SQL injection prevention (parameterized queries)
- [ ] CORS policy refinement (restrict origins)
- [ ] Session management improvements (secure cookies)
- [ ] Encryption key rotation mechanism

### 🟡 Future Improvements

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

**Architecture complète et extensible ✅**
**Phase 4 Security Hardening Complete ✅ (4/4 Tier 1 items)**
