# 🚀 Guide Rapide de Démarrage

Bienvenue dans votre interface de gestion du parc informatique Jadus Audit!

## ⏱️ Démarrage en 5 minutes

### 1. Préparer l'environnement

**Windows (PowerShell):**
```powershell
cd server_C2
python -m venv venv                    # Créer l'env si nécessaire
.\venv\Scripts\Activate.ps1            # Activer l'environnement virtuel
pip install -r requirements.txt        # Installer les dépendances
```

**Linux/macOS (Bash):**
```bash
cd server_C2
python -m venv venv              # Créer l'env si nécessaire
source venv/bin/activate         # Activer l'environnement virtuel
pip install -r requirements.txt  # Installer les dépendances
```

### 2. Configurer la base de données

#### 📊 Mode In-Memory (Développement - par défaut)

C'est déjà configuré! Les données sont stockées en mémoire. Parfait pour tester.

#### 🔧 Mode MongoDB (Production)

Voir [MONGODB.md](MONGODB.md) pour une configuration complète.

Rapidement:
```bash
# Lancer MongoDB (Docker)
docker run -d --name mongodb -p 27017:27017 mongo:latest

# Configurer .env
DATABASE_MODE=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=c2_server
```

### 3. Démarrer l'API (Terminal 1)

```powershell
python main.py
```

**Résultat attendu:**
```
🟢 Database mode: In-Memory (development)
✅ In-Memory database initialized
Routes registered successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

L'API démarre sur **http://localhost:8000**

### 4. Accéder au Dashboard

Vous avez 2 options:

**Option A: Serveur Web Local**
```bash
# Terminal 2
cd server_C2/web
python -m http.server 8080
```
Accédez à: **http://localhost:8080**

**Option B: Swagger UI**
Accédez directement à: **http://localhost:8000/docs**

### 5. C'est parti! 🎉

Le dashboard s'affiche avec:
- ✅ Vue d'ensemble de la conformité
- ✅ Liste des agents
- ✅ Alertes du système
- ✅ Boutons pour lancer des audits

---

## 📊 Dashboard - Guide Rapide

### 🟢 Santé Globale (En haut)

```
Agents Actifs: 10/12      Taux de Succès: 93.5%
Agents Inactifs: 2        Beacons: 5,234
```

**Si vous voyez du rouge**: Problèmes détectés → Consultez les "Alertes"

### 🟡 Alertes (Section Alertes)

```
❌ CRITICAL: Agent "PC-AUDIT-05" inactif depuis 3h
⚠️ WARNING: Agent "PC-AUDIT-08" lent (pas de réponse depuis 45min)
```

**Action requise**: Enquêter sur les agents problématiques

### 👥 État des Agents (Section Agents)

Tableau avec chaque machine:
- **Statut**: active/inactive/compromised
- **Hostname**: Serveur/PC
- **Succès**: Pourcentage de tâches réussies (barre verte)
- **Bouton 🚀 Audit**: Lancer un audit maintenant

### ❌ Agents Hors Ligne (Section Offline)

Machines inaccessibles avec durée d'inactivité.

---

## 🚀 Lancer un Audit

### Cas 1: Audit Simple

1. Trouvez l'agent dans **"État des Agents"**
2. Cliquez sur **🚀 Audit**
3. Sélectionnez une commande (ex: `Get-AuditPolicy`)
4. Cliquez **✓ Lancer l'Audit**

✅ L'audit est envoyé à l'agent!

### Cas 2: Audit Personnalisé

1. Cliquez **🚀 Audit** → Sélectionnez "Personnalisée"
2. Entrez votre commande PowerShell
3. Cliquez **✓ Lancer l'Audit**

**Exemples de commandes:**
```powershell
Get-Process | Select-Object Name, CPU | ConvertTo-Json
Get-EventLog -LogName System -Newest 100 | ConvertTo-Json
Get-LocalGroupMember -Group "Administrators" | ConvertTo-Json
```

---

## 🔗 Documentation Complète

Pour plus de détails, consultez:

- 🏗️ [Architecture](../architecture/ARCHITECTURE.md) - Design global du système
- 🔐 [Sécurité](../architecture/SECURITY.md) - Système de sécurité Phase 5
- 📡 [API](../api/API.md) - Documentation des endpoints
- 🧪 [Tests](../testing/TESTING.md) - Guides de test
- 💾 [MongoDB](./MONGODB.md) - Configuration production

---

## ✅ Checklist Startup

- [ ] Python 3.8+ installé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] API lancée (`python main.py`)
- [ ] Dashboard accessible (`http://localhost:8000/docs` ou web)
- [ ] Au moins 1 agent enregistré

---

## 🐛 Troubleshooting

### API ne démarre pas

```bash
# Vérifier l'erreur
python main.py

# Créer l'env virtuel si besoin
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/macOS

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Port 8000 déjà utilisé

```bash
# Windows: Trouver le processus
netstat -ano | findstr :8000

# Linux/macOS:
lsof -i :8000

# Lancer sur un autre port
python main.py --port 8001
```

### Dashboard vide (pas d'agents)

Les agents doivent s'enregistrer d'abord. Lancez un agent PowerShell:
```powershell
# Sur un agent client
.\agent_real.ps1
```

Voir le script dans `/scripts/agent/agent_real.ps1`

---

## 📱 Tester les APIs avec PowerShell

```powershell
# Enregistrer un agent
$body = @{
    agent_name = "TEST-AGENT-1"
    os_version = "Windows 10"
    hostname = "DESKTOP-TEST"
    username = "admin"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/enroll" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body

$response
```

---

**🎯 Vous êtes prêt!** Explorez le dashboard et lancez vos premiers audits.
