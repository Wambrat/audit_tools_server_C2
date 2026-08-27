# jadus Dashboard - Application Web Vue.js

Interface web pour surveiller la conformitÃ© du parc informatique et lancer des audits de sÃ©curitÃ©.

## ðŸŽ¯ FonctionnalitÃ©s

- **Dashboard global**: Vue d'ensemble de la santÃ© du systÃ¨me
- **Surveillance des agents**: Liste de tous les agents avec leur statut
- **Agents hors-ligne**: Tableau dÃ©diÃ© aux machines non disponibles
- **Alertes**: DÃ©tection automatique des problÃ¨mes (agents inactifs, tÃ¢ches en retard, etc.)
- **Lancement d'audits**: Bouton pour crÃ©er des tÃ¢ches d'audit par agent
- **Statistiques**: Taux de succÃ¨s, temps d'exÃ©cution, performance
- **Auto-rafraÃ®chissement**: Les donnÃ©es se mettent Ã  jour toutes les 30 secondes
- **ðŸ” Admin Panel**: Dashboard d'administration avec accÃ¨s JWT protÃ©gÃ©
- **Admin Login**: Authentification sÃ©curisÃ©e pour les administrateurs

## ðŸ“ Structure du Projet

```
web/
â”œâ”€â”€ index.html            # Point d'entrÃ©e HTML - Dashboard principal
â”œâ”€â”€ admin-login.html      # Page de connexion administrateur
â”œâ”€â”€ admin.html            # Dashboard d'administration
â”œâ”€â”€ results.html          # Page des rÃ©sultats dÃ©taillÃ©s
â”œâ”€â”€ js/
â”‚   â”œâ”€â”€ api.js            # Client API pour communiquer avec FastAPI
â”‚   â”œâ”€â”€ app.js            # Application Vue.js principale
â”‚   â”œâ”€â”€ admin-login.js    # Logic Vue pour authentification admin
â”‚   â””â”€â”€ admin-dashboard.js # Logic Vue pour dashboard admin
â”œâ”€â”€ css/
â”‚   â””â”€â”€ style.css         # Styles CSS (dashboard principal)
â””â”€â”€ README.md             # Ce fichier
```

## ðŸ“„ Pages Disponibles

### 1. `index.html` - Dashboard Principal
Le point d'entrÃ©e du systÃ¨me. Affiche:
- Vue d'ensemble de la santÃ© globale
- Statistiques en temps rÃ©el
- Liste des agents actifs
- Alertes du systÃ¨me
- Lien d'accÃ¨s au dashboard admin

**AccÃ¨s:** `http://localhost:8080/index.html`

### 2. `admin-login.html` - Connexion Administrateur
Page sÃ©curisÃ©e de connexion pour les administrateurs.

**Features:**
- Formulaire d'authentification moderne
- Validation cÃ´tÃ© client
- Gestion des erreurs (401, 429, etc.)
- Option "Se souvenir de moi"
- Redirection automatique aprÃ¨s connexion

**AccÃ¨s:** `http://localhost:8080/admin-login.html`

**Identifiants par dÃ©faut:**
```
Username: admin
Password: changeme
```

### 3. `admin.html` - Dashboard d'Administration
Panneau complet d'administration avec authentification JWT.

**Sections:**
- ðŸ“Š Vue d'ensemble: Statistiques systÃ¨me
- ðŸ‘¥ Agents: Gestion et surveillance des agents
- âœ“ TÃ¢ches: Gestion des tÃ¢ches d'audit
- ðŸ“‹ RÃ©sultats: Visualisation des rÃ©sultats d'audit
- ðŸš¨ Alertes: Alertes systÃ¨me et santÃ©
- âš™ï¸ ParamÃ¨tres: Configuration et actions admin

**AccÃ¨s:** `http://localhost:8080/admin.html` (authentification requise)

### 4. `results.html` - RÃ©sultats DÃ©taillÃ©s
Page de visualisation dÃ©taillÃ©e des rÃ©sultats d'audit.

**AccÃ¨s:** `http://localhost:8080/results.html`

## ðŸš€ Lancement

- Le serveur FastAPI doit Ãªtre en cours d'exÃ©cution sur `http://localhost:8000`
- Un serveur HTTP local (optionnel pour le dÃ©veloppement)

### Option 1: Lancer avec Python (Simple)

```bash
# Du rÃ©pertoire web/
python -m http.server 8080
```

Puis accÃ©dez Ã : `http://localhost:8080`

### Option 2: Lancer avec Node.js (si disponible)

```bash
# Installer http-server globalement
npm install -g http-server

# Lancer le serveur depuis le rÃ©pertoire web/
http-server -p 8080
```

### Option 3: Ouvrir directement dans le navigateur

Double-cliquez sur `index.html` pour l'ouvrir directement (fonctionne sur les fichiers locaux en mode CDN).

### Configuration API

Par dÃ©faut, l'application se connecte Ã  `http://localhost:8000/api`.

Pour modifier l'URL de l'API, Ã©ditez le fichier `js/api.js`:

```javascript
const API_BASE_URL = 'http://votre-serveur:8000/api';
```

## ðŸ“Š Dashboard - Sections

### 1. SantÃ© Globale du SystÃ¨me

Affiche les statistiques clÃ©s:
- **Agents Actifs**: Nombre d'agents en ligne
- **Agents Inactifs**: Nombre d'agents hors-ligne
- **Taux de SuccÃ¨s**: Pourcentage de tÃ¢ches rÃ©ussies
- **TÃ¢ches**: RÃ©partition par statut (en attente, assignÃ©es, complÃ©tÃ©es, Ã©chouÃ©es)
- **Temps Moyen**: Temps d'exÃ©cution moyen des tÃ¢ches

### 2. Alertes du SystÃ¨me

Liste des problÃ¨mes dÃ©tectÃ©s automatiquement:
- **ðŸ”´ CRITICAL**: Agents inactifs depuis 2+ heures, agents jamais connectÃ©s
- **ðŸŸ¡ WARNING**: Agents lents (30+ min sans beacon), tÃ¢ches en retard
- **ðŸŸ¢ OK**: SystÃ¨me sain

### 3. Ã‰tat des Agents

Tableau dÃ©taillÃ© de chaque agent avec:
- Nom et statut
- Hostname et OS
- Utilisateur et date d'enregistrement
- Nombre de beacons et tÃ¢ches
- Taux de succÃ¨s (avec barre de progression)
- Bouton "ðŸš€ Audit" pour lancer un audit

### 4. Agents Hors Ligne

Tableau spÃ©cifique listÃ© les machines inaccessibles avec:
- Nombre d'heures/minutes d'inactivitÃ©
- Boutons de retry pour forcer la reconnexion

### 5. RÃ©sumÃ© des TÃ¢ches

Statistiques agrÃ©gÃ©es sur les tÃ¢ches en cours/complÃ©tÃ©es.

## ðŸ”§ Utilisation

### Lancer un Audit

1. Localisez l'agent dans la section "Ã‰tat des Agents"
2. Cliquez sur le bouton **"ðŸš€ Audit"**
3. SÃ©lectionnez une commande parmi les options proposÃ©es:
   - `Get-AuditPolicy` - Politiques d'audit Windows
   - `Get-EventLog` - Logs d'Ã©vÃ©nements
   - `Get-LocalUser` - Utilisateurs locaux
   - `Get-Service` - Services Windows
   - `Get-Process` - Processus actifs
   - `Get-NetConnectionProfile` - ConnectivitÃ© rÃ©seau
   - `Get-WindowsFeature` - RÃ´les/fonctionnalitÃ©s
   - PersonnalisÃ©e - Entrez une commande PowerShell

4. SÃ©lectionnez la prioritÃ© (Normal / Haute / Critique)
5. Cliquez sur **"âœ“ Lancer l'Audit"**

L'audit est crÃ©Ã© et envoyÃ© Ã  l'agent. Les rÃ©sultats seront visibles aprÃ¨s exÃ©cution.

### RafraÃ®chir les DonnÃ©es

- **Manuel**: Cliquez sur le bouton **"ðŸ”„ RafraÃ®chir"**
- **Automatique**: Les donnÃ©es se mettent Ã  jour tous les 30 secondes

## ðŸŽ¨ ThÃ¨me & Styling

L'application utilise un thÃ¨me professionnel avec:
- Couleurs standard (bleu pour les actions, vert pour le succÃ¨s, rouge pour les erreurs)
- Design responsive (adaptable Ã  tous les Ã©crans)
- Animations fluides et transitions
- AccessibilitÃ© optimisÃ©e

## ðŸ”Œ API UtilisÃ©e

L'application communique avec les endpoints suivants:

| Endpoint | UtilitÃ© |
|----------|---------|
| `GET /monitoring/overview` | Vue d'ensemble globale |
| `GET /monitoring/agents` | DÃ©tails par agent |
| `GET /monitoring/tasks` | Statistiques de tÃ¢ches |
| `GET /monitoring/results` | Statistiques de rÃ©sultats |
| `GET /monitoring/alerts` | Alertes du systÃ¨me |
| `POST /tasks/{agent_id}` | CrÃ©er une nouvelle tÃ¢che |

## ðŸ“ Notes Techniques

### DÃ©pendances

- **Vue.js 3** (CDN): Framework web rÃ©actif
- **JavaScript natif**: Pas de compilation nÃ©cessaire
- **CSS3**: Styling moderne et responsive

### Navigateurs SupportÃ©s

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### CORS

Si vous lancez l'application depuis un domaine diffÃ©rent du serveur API, assurez-vous que CORS est correctement configurÃ© dans `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## ðŸ› Troubleshooting

### Erreur "Impossible de charger les donnÃ©es"

**Cause**: L'API n'est pas accessible

**Solution**:
1. VÃ©rifiez que le serveur FastAPI est en cours d'exÃ©cution
2. VÃ©rifiez l'URL de l'API dans `js/api.js`
3. VÃ©rifiez la configuration CORS

### Les donnÃ©es ne se mettent pas Ã  jour

**Cause**: L'auto-rafraÃ®chissement pourrait Ãªtre bloquÃ©

**Solution**:
1. Cliquez manuellement sur "ðŸ”„ RafraÃ®chir"
2. VÃ©rifiez la console (F12) pour les erreurs
3. VÃ©rifiez la connexion rÃ©seau

### Les audits ne se lancent pas

**Cause**: L'agent pourrait Ãªtre inactif

**Solution**:
1. VÃ©rifiez que l'agent a le statut "active"
2. Essayez avec un agent en ligne
3. VÃ©rifiez les logs de l'API pour les erreurs

## ðŸ“š Documentation ComplÃ¨te

Pour plus de dÃ©tails sur l'API, consultez [../README.md](../README.md).

## ðŸ“„ Licence

Ã€ dÃ©finir selon votre projet.

