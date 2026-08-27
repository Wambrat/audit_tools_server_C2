# ðŸ› ï¸ jadus Agent MSI - Guide Rapide

## ðŸ“‚ Contenu du dossier

| Fichier | Description |
|---------|-------------|
| `jadusAgent.wxs` | Configuration WiX pour le MSI |
| `config.json` | Fichier de configuration (ServerUrl, BeaconInterval) |
| `launcher.ps1` | Script qui charge la config et lance l'agent |
| `build-msi.ps1` | Script de compilation MSI |
| `install-scheduled-task.ps1` | Script pour crÃ©er la tÃ¢che planifiÃ©e |
| `INSTALLATION_GUIDE.md` | Guide complet d'installation |
| `agent_active.ps1` | Ã€ copier depuis le rÃ©pertoire racine |

---

## ðŸš€ DÃ©marrage rapide (5 min)

### 1. Copier l'agent
```powershell
Copy-Item "..\agent_active.ps1" ".\"
```

### 2. Compiler le MSI
```powershell
# Avoir WiX installÃ© d'abord: https://github.com/wixtoolset/wix3/releases
.\build-msi.ps1
```

### 3. Configurer
Ã‰diter `config.json`:
```json
"serverUrl": "http://votre-serveur-jadus:8000/api"
```

### 4. Installer
```powershell
msiexec /i jadusAgent.msi /quiet /norestart
```

### 5. CrÃ©er la tÃ¢che planifiÃ©e
```powershell
.\install-scheduled-task.ps1
```

---

## âœ… VÃ©rifier

```powershell
# VÃ©rifier la tÃ¢che
Get-ScheduledTask -TaskName "jadusAgentBeacon"

# Voir les logs
Get-Content "C:\Program Files\jadusAgent\logs\agent.log" -Tail 50

# Tester
Start-ScheduledTask -TaskName "jadusAgentBeacon"
```

---

## ðŸ“– Documentation complÃ¨te

Voir `INSTALLATION_GUIDE.md` pour tous les dÃ©tails.

---

## âš™ï¸ Configuration (config.json)

```json
{
  "agent": {
    "serverUrl": "http://localhost:8000/api",     // URL du serveur jadus
    "beaconInterval": 30,                         // FrÃ©quence en secondes
    "logFile": "%PROGRAMFILES%\\jadusAgent\\logs\\agent.log",
    "logLevel": "INFO"
  },
  "scheduled_task": {
    "taskName": "jadusAgentBeacon",                  // Nom de la tÃ¢che
    "triggerInterval": 30,                        // Intervalle en secondes
    "runWithHighestPrivileges": true,
    "runUser": "SYSTEM"                           // Utilisateur d'exÃ©cution
  }
}
```

---

## ðŸ”„ Workflow complet

```
1. Ã‰diter config.json avec vos paramÃ¨tres
   â†“
2. Copier agent_active.ps1
   â†“
3. ./build-msi.ps1  (crÃ©e jadusAgent.msi)
   â†“
4. msiexec /i jadusAgent.msi /quiet
   â†“
5. ./install-scheduled-task.ps1
   â†“
6. âœ… Agent actif et s'exÃ©cute toutes les 30 secondes
```

---

## ðŸŽ¯ CaractÃ©ristiques

âœ… **Installation silencieuse** - Pas d'interface, discret  
âœ… **Configuration flexible** - Modifiable via JSON  
âœ… **TÃ¢che planifiÃ©e** - S'exÃ©cute toutes les 30s (configurable)  
âœ… **Logs structurÃ©s** - `C:\Program Files\jadusAgent\logs\agent.log`  
âœ… **PrivilÃ¨ges SYSTEM** - ExÃ©cution en tant qu'administrateur  
âœ… **Auto-dÃ©marrage** - S'exÃ©cute mÃªme aprÃ¨s reboot  

---

## ðŸ› Aide

- Ã‰diter `config.json` si l'URL du serveur change
- Voir `INSTALLATION_GUIDE.md` pour le dÃ©ploiement en masse (GPO/SCCM)
- Les logs se trouvent dans `C:\Program Files\jadusAgent\logs\`

