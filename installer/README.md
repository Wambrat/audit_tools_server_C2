# 🛠️ Jadus Agent MSI - Guide Rapide

## 📂 Contenu du dossier

| Fichier | Description |
|---------|-------------|
| `JadusAgent.wxs` | Configuration WiX pour le MSI |
| `config.json` | Fichier de configuration (ServerUrl, BeaconInterval) |
| `launcher.ps1` | Script qui charge la config et lance l'agent |
| `build-msi.ps1` | Script de compilation MSI |
| `install-scheduled-task.ps1` | Script pour créer la tâche planifiée |
| `INSTALLATION_GUIDE.md` | Guide complet d'installation |
| `agent_active.ps1` | À copier depuis le répertoire racine |

---

## 🚀 Démarrage rapide (5 min)

### 1. Copier l'agent
```powershell
Copy-Item "..\agent_active.ps1" ".\"
```

### 2. Compiler le MSI
```powershell
# Avoir WiX installé d'abord: https://github.com/wixtoolset/wix3/releases
.\build-msi.ps1
```

### 3. Configurer
Éditer `config.json`:
```json
"serverUrl": "http://votre-serveur-c2:8000/api"
```

### 4. Installer
```powershell
msiexec /i JadusAgent.msi /quiet /norestart
```

### 5. Créer la tâche planifiée
```powershell
.\install-scheduled-task.ps1
```

---

## ✅ Vérifier

```powershell
# Vérifier la tâche
Get-ScheduledTask -TaskName "JadusAgentBeacon"

# Voir les logs
Get-Content "C:\Program Files\JadusAgent\logs\agent.log" -Tail 50

# Tester
Start-ScheduledTask -TaskName "JadusAgentBeacon"
```

---

## 📖 Documentation complète

Voir `INSTALLATION_GUIDE.md` pour tous les détails.

---

## ⚙️ Configuration (config.json)

```json
{
  "agent": {
    "serverUrl": "http://localhost:8000/api",     // URL du serveur Jadus Audit
    "beaconInterval": 30,                         // Fréquence en secondes
    "logFile": "%PROGRAMFILES%\\JadusAgent\\logs\\agent.log",
    "logLevel": "INFO"
  },
  "scheduled_task": {
    "taskName": "JadusAgentBeacon",                  // Nom de la tâche
    "triggerInterval": 30,                        // Intervalle en secondes
    "runWithHighestPrivileges": true,
    "runUser": "SYSTEM"                           // Utilisateur d'exécution
  }
}
```

---

## 🔄 Workflow complet

```
1. Éditer config.json avec vos paramètres
   ↓
2. Copier agent_active.ps1
   ↓
3. ./build-msi.ps1  (crée JadusAgent.msi)
   ↓
4. msiexec /i JadusAgent.msi /quiet
   ↓
5. ./install-scheduled-task.ps1
   ↓
6. ✅ Agent actif et s'exécute toutes les 30 secondes
```

---

## 🎯 Caractéristiques

✅ **Installation silencieuse** - Pas d'interface, discret  
✅ **Configuration flexible** - Modifiable via JSON  
✅ **Tâche planifiée** - S'exécute toutes les 30s (configurable)  
✅ **Logs structurés** - `C:\Program Files\JadusAgent\logs\agent.log`  
✅ **Privilèges SYSTEM** - Exécution en tant qu'administrateur  
✅ **Auto-démarrage** - S'exécute même après reboot  

---

## 🐛 Aide

- Éditer `config.json` si l'URL du serveur change
- Voir `INSTALLATION_GUIDE.md` pour le déploiement en masse (GPO/SCCM)
- Les logs se trouvent dans `C:\Program Files\JadusAgent\logs\`
