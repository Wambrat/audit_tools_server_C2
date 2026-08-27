# ðŸš€ Guide Rapide de DÃ©marrage

Bienvenue dans votre interface de gestion du parc informatique Jadus Audit!

## â±ï¸ DÃ©marrage en 5 minutes

### 1. PrÃ©parer l'environnement

**Windows (PowerShell):**
```powershell
cd jadus
python -m venv venv                    # CrÃ©er l'env si nÃ©cessaire
.\venv\Scripts\Activate.ps1            # Activer l'environnement virtuel
pip install -r requirements.txt        # Installer les dÃ©pendances
```

**Linux/macOS (Bash):**
```bash
cd jadus
python -m venv venv              # CrÃ©er l'env si nÃ©cessaire
source venv/bin/activate         # Activer l'environnement virtuel
pip install -r requirements.txt  # Installer les dÃ©pendances
```

### 2. Configurer la base de donnÃ©es

#### ðŸ“Š Mode In-Memory (DÃ©veloppement - par dÃ©faut)

C'est dÃ©jÃ  configurÃ©! Les donnÃ©es sont stockÃ©es en mÃ©moire. Parfait pour tester.

#### ðŸ”§ Mode MongoDB (Production)

Voir [MONGODB.md](MONGODB.md) pour une configuration complÃ¨te.

Rapidement:
```bash
# Lancer MongoDB (Docker)
docker run -d --name mongodb -p 27017:27017 mongo:latest

# Configurer .env
DATABASE_MODE=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=jadus_server
```

### 3. DÃ©marrer l'API (Terminal 1)

```powershell
python main.py
```

**RÃ©sultat attendu:**
```
ðŸŸ¢ Database mode: In-Memory (development)
âœ… In-Memory database initialized
Routes registered successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

L'API dÃ©marre sur **http://localhost:8000**

### 4. AccÃ©der au Dashboard

Vous avez 2 options:

**Option A: Serveur Web Local**
```bash
# Terminal 2
cd jadus/web
python -m http.server 8080
```
AccÃ©dez Ã : **http://localhost:8080**

**Option B: Swagger UI**
AccÃ©dez directement Ã : **http://localhost:8000/docs**

### 5. C'est parti! ðŸŽ‰

Le dashboard s'affiche avec:
- âœ… Vue d'ensemble de la conformitÃ©
- âœ… Liste des agents
- âœ… Alertes du systÃ¨me
- âœ… Boutons pour lancer des audits

---

## ðŸ“Š Dashboard - Guide Rapide

### ðŸŸ¢ SantÃ© Globale (En haut)

```
Agents Actifs: 10/12      Taux de SuccÃ¨s: 93.5%
Agents Inactifs: 2        Beacons: 5,234
```

**Si vous voyez du rouge**: ProblÃ¨mes dÃ©tectÃ©s â†’ Consultez les "Alertes"

### ðŸŸ¡ Alertes (Section Alertes)

```
âŒ CRITICAL: Agent "PC-AUDIT-05" inactif depuis 3h
âš ï¸ WARNING: Agent "PC-AUDIT-08" lent (pas de rÃ©ponse depuis 45min)
```

**Action requise**: EnquÃªter sur les agents problÃ©matiques

### ðŸ‘¥ Ã‰tat des Agents (Section Agents)

Tableau avec chaque machine:
- **Statut**: active/inactive/compromised
- **Hostname**: Serveur/PC
- **SuccÃ¨s**: Pourcentage de tÃ¢ches rÃ©ussies (barre verte)
- **Bouton ðŸš€ Audit**: Lancer un audit maintenant

### âŒ Agents Hors Ligne (Section Offline)

Machines inaccessibles avec durÃ©e d'inactivitÃ©.

---

## ðŸš€ Lancer un Audit

### Cas 1: Audit Simple

1. Trouvez l'agent dans **"Ã‰tat des Agents"**
2. Cliquez sur **ðŸš€ Audit**
3. SÃ©lectionnez une commande (ex: `Get-AuditPolicy`)
4. Cliquez **âœ“ Lancer l'Audit**

âœ… L'audit est envoyÃ© Ã  l'agent!

### Cas 2: Audit PersonnalisÃ©

1. Cliquez **ðŸš€ Audit** â†’ SÃ©lectionnez "PersonnalisÃ©e"
2. Entrez votre commande PowerShell
3. Cliquez **âœ“ Lancer l'Audit**

**Exemples de commandes:**
```powershell
Get-Process | Select-Object Name, CPU | ConvertTo-Json
Get-EventLog -LogName System -Newest 100 | ConvertTo-Json
Get-LocalGroupMember -Group "Administrators" | ConvertTo-Json
```

---

## ðŸ”— Documentation ComplÃ¨te

Pour plus de dÃ©tails, consultez:

- ðŸ—ï¸ [Architecture](../architecture/ARCHITECTURE.md) - Design global du systÃ¨me
- ðŸ” [SÃ©curitÃ©](../architecture/SECURITY.md) - SystÃ¨me de sÃ©curitÃ© Phase 5
- ðŸ“¡ [API](../api/API.md) - Documentation des endpoints
- ðŸ§ª [Tests](../testing/TESTING.md) - Guides de test
- ðŸ’¾ [MongoDB](./MONGODB.md) - Configuration production

---

## âœ… Checklist Startup

- [ ] Python 3.8+ installÃ©
- [ ] DÃ©pendances installÃ©es (`pip install -r requirements.txt`)
- [ ] API lancÃ©e (`python main.py`)
- [ ] Dashboard accessible (`http://localhost:8000/docs` ou web)
- [ ] Au moins 1 agent enregistrÃ©

---

## ðŸ› Troubleshooting

### API ne dÃ©marre pas

```bash
# VÃ©rifier l'erreur
python main.py

# CrÃ©er l'env virtuel si besoin
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/macOS

# RÃ©installer les dÃ©pendances
pip install -r requirements.txt
```

### Port 8000 dÃ©jÃ  utilisÃ©

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

## ðŸ“± Tester les APIs avec PowerShell

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

**ðŸŽ¯ Vous Ãªtes prÃªt!** Explorez le dashboard et lancez vos premiers audits.

