# C2 Dashboard - Application Web Vue.js

Interface web pour surveiller la conformité du parc informatique et lancer des audits de sécurité.

## 🎯 Fonctionnalités

- **Dashboard global**: Vue d'ensemble de la santé du système
- **Surveillance des agents**: Liste de tous les agents avec leur statut
- **Agents hors-ligne**: Tableau dédié aux machines non disponibles
- **Alertes**: Détection automatique des problèmes (agents inactifs, tâches en retard, etc.)
- **Lancement d'audits**: Bouton pour créer des tâches d'audit par agent
- **Statistiques**: Taux de succès, temps d'exécution, performance
- **Auto-rafraîchissement**: Les données se mettent à jour toutes les 30 secondes
- **🔐 Admin Panel**: Dashboard d'administration avec accès JWT protégé
- **Admin Login**: Authentification sécurisée pour les administrateurs

## 📁 Structure du Projet

```
web/
├── index.html            # Point d'entrée HTML - Dashboard principal
├── admin-login.html      # Page de connexion administrateur
├── admin.html            # Dashboard d'administration
├── results.html          # Page des résultats détaillés
├── js/
│   ├── api.js            # Client API pour communiquer avec FastAPI
│   ├── app.js            # Application Vue.js principale
│   ├── admin-login.js    # Logic Vue pour authentification admin
│   └── admin-dashboard.js # Logic Vue pour dashboard admin
├── css/
│   └── style.css         # Styles CSS (dashboard principal)
└── README.md             # Ce fichier
```

## 📄 Pages Disponibles

### 1. `index.html` - Dashboard Principal
Le point d'entrée du système. Affiche:
- Vue d'ensemble de la santé globale
- Statistiques en temps réel
- Liste des agents actifs
- Alertes du système
- Lien d'accès au dashboard admin

**Accès:** `http://localhost:8080/index.html`

### 2. `admin-login.html` - Connexion Administrateur
Page sécurisée de connexion pour les administrateurs.

**Features:**
- Formulaire d'authentification moderne
- Validation côté client
- Gestion des erreurs (401, 429, etc.)
- Option "Se souvenir de moi"
- Redirection automatique après connexion

**Accès:** `http://localhost:8080/admin-login.html`

**Identifiants par défaut:**
```
Username: admin
Password: changeme
```

### 3. `admin.html` - Dashboard d'Administration
Panneau complet d'administration avec authentification JWT.

**Sections:**
- 📊 Vue d'ensemble: Statistiques système
- 👥 Agents: Gestion et surveillance des agents
- ✓ Tâches: Gestion des tâches d'audit
- 📋 Résultats: Visualisation des résultats d'audit
- 🚨 Alertes: Alertes système et santé
- ⚙️ Paramètres: Configuration et actions admin

**Accès:** `http://localhost:8080/admin.html` (authentification requise)

### 4. `results.html` - Résultats Détaillés
Page de visualisation détaillée des résultats d'audit.

**Accès:** `http://localhost:8080/results.html`

## 🚀 Lancement

- Le serveur FastAPI doit être en cours d'exécution sur `http://localhost:8000`
- Un serveur HTTP local (optionnel pour le développement)

### Option 1: Lancer avec Python (Simple)

```bash
# Du répertoire web/
python -m http.server 8080
```

Puis accédez à: `http://localhost:8080`

### Option 2: Lancer avec Node.js (si disponible)

```bash
# Installer http-server globalement
npm install -g http-server

# Lancer le serveur depuis le répertoire web/
http-server -p 8080
```

### Option 3: Ouvrir directement dans le navigateur

Double-cliquez sur `index.html` pour l'ouvrir directement (fonctionne sur les fichiers locaux en mode CDN).

### Configuration API

Par défaut, l'application se connecte à `http://localhost:8000/api`.

Pour modifier l'URL de l'API, éditez le fichier `js/api.js`:

```javascript
const API_BASE_URL = 'http://votre-serveur:8000/api';
```

## 📊 Dashboard - Sections

### 1. Santé Globale du Système

Affiche les statistiques clés:
- **Agents Actifs**: Nombre d'agents en ligne
- **Agents Inactifs**: Nombre d'agents hors-ligne
- **Taux de Succès**: Pourcentage de tâches réussies
- **Tâches**: Répartition par statut (en attente, assignées, complétées, échouées)
- **Temps Moyen**: Temps d'exécution moyen des tâches

### 2. Alertes du Système

Liste des problèmes détectés automatiquement:
- **🔴 CRITICAL**: Agents inactifs depuis 2+ heures, agents jamais connectés
- **🟡 WARNING**: Agents lents (30+ min sans beacon), tâches en retard
- **🟢 OK**: Système sain

### 3. État des Agents

Tableau détaillé de chaque agent avec:
- Nom et statut
- Hostname et OS
- Utilisateur et date d'enregistrement
- Nombre de beacons et tâches
- Taux de succès (avec barre de progression)
- Bouton "🚀 Audit" pour lancer un audit

### 4. Agents Hors Ligne

Tableau spécifique listé les machines inaccessibles avec:
- Nombre d'heures/minutes d'inactivité
- Boutons de retry pour forcer la reconnexion

### 5. Résumé des Tâches

Statistiques agrégées sur les tâches en cours/complétées.

## 🔧 Utilisation

### Lancer un Audit

1. Localisez l'agent dans la section "État des Agents"
2. Cliquez sur le bouton **"🚀 Audit"**
3. Sélectionnez une commande parmi les options proposées:
   - `Get-AuditPolicy` - Politiques d'audit Windows
   - `Get-EventLog` - Logs d'événements
   - `Get-LocalUser` - Utilisateurs locaux
   - `Get-Service` - Services Windows
   - `Get-Process` - Processus actifs
   - `Get-NetConnectionProfile` - Connectivité réseau
   - `Get-WindowsFeature` - Rôles/fonctionnalités
   - Personnalisée - Entrez une commande PowerShell

4. Sélectionnez la priorité (Normal / Haute / Critique)
5. Cliquez sur **"✓ Lancer l'Audit"**

L'audit est créé et envoyé à l'agent. Les résultats seront visibles après exécution.

### Rafraîchir les Données

- **Manuel**: Cliquez sur le bouton **"🔄 Rafraîchir"**
- **Automatique**: Les données se mettent à jour tous les 30 secondes

## 🎨 Thème & Styling

L'application utilise un thème professionnel avec:
- Couleurs standard (bleu pour les actions, vert pour le succès, rouge pour les erreurs)
- Design responsive (adaptable à tous les écrans)
- Animations fluides et transitions
- Accessibilité optimisée

## 🔌 API Utilisée

L'application communique avec les endpoints suivants:

| Endpoint | Utilité |
|----------|---------|
| `GET /monitoring/overview` | Vue d'ensemble globale |
| `GET /monitoring/agents` | Détails par agent |
| `GET /monitoring/tasks` | Statistiques de tâches |
| `GET /monitoring/results` | Statistiques de résultats |
| `GET /monitoring/alerts` | Alertes du système |
| `POST /tasks/{agent_id}` | Créer une nouvelle tâche |

## 📝 Notes Techniques

### Dépendances

- **Vue.js 3** (CDN): Framework web réactif
- **JavaScript natif**: Pas de compilation nécessaire
- **CSS3**: Styling moderne et responsive

### Navigateurs Supportés

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### CORS

Si vous lancez l'application depuis un domaine différent du serveur API, assurez-vous que CORS est correctement configuré dans `main.py`:

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

## 🐛 Troubleshooting

### Erreur "Impossible de charger les données"

**Cause**: L'API n'est pas accessible

**Solution**:
1. Vérifiez que le serveur FastAPI est en cours d'exécution
2. Vérifiez l'URL de l'API dans `js/api.js`
3. Vérifiez la configuration CORS

### Les données ne se mettent pas à jour

**Cause**: L'auto-rafraîchissement pourrait être bloqué

**Solution**:
1. Cliquez manuellement sur "🔄 Rafraîchir"
2. Vérifiez la console (F12) pour les erreurs
3. Vérifiez la connexion réseau

### Les audits ne se lancent pas

**Cause**: L'agent pourrait être inactif

**Solution**:
1. Vérifiez que l'agent a le statut "active"
2. Essayez avec un agent en ligne
3. Vérifiez les logs de l'API pour les erreurs

## 📚 Documentation Complète

Pour plus de détails sur l'API, consultez [../README.md](../README.md).

## 📄 Licence

À définir selon votre projet.
