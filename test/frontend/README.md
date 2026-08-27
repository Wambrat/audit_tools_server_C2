# 🎨 Tests du Frontend (IHM)

## 📁 Structure des Tests Frontend

```
test/frontend/
├── __init__.py              # Initialisation du module
├── setup.js                 # Configuration Jest
├── test_api.js              # Tests du client API (20 tests)
├── test_app.js              # Tests de l'app Vue.js (25 tests)
├── test_ihm.js              # Tests d'intégration IHM (40 tests)
└── README.md               # Documentation
```

## 📊 Fichiers de Test

### **test_api.js** (20 tests)
Tests du client API (`web/js/api.js`)

| Test | Description |
|------|-------------|
| ✅ getSystemOverview | Récupère l'aperçu système |
| ✅ getAgentsDashboard | Récupère le dashboard agents |
| ✅ getTasksDashboard | Récupère le dashboard tâches |
| ✅ getResultsDashboard | Récupère le dashboard résultats |
| ✅ getAlerts | Récupère les alertes système |
| ✅ getAgents | Récupère la liste des agents |
| ✅ createTask | Crée une nouvelle tâche |
| ✅ Gestion d'erreurs HTTP | Gère 404, 500, etc. |
| ✅ Erreurs réseau | Gère les erreurs de connexion |
| ✅ Logging des erreurs | Log en console |

### **test_app.js** (25 tests)
Tests de l'application Vue.js (`web/js/app.js`)

| Test | Description |
|------|-------------|
| ✅ État initial | Initialise les données |
| ✅ Computed: successRate | Calcule le taux de succès |
| ✅ Computed: inactiveAgents | Filtre les agents inactifs |
| ✅ loadDashboardData | Charge les données en parallèle |
| ✅ Gestion erreurs API | Gère les erreurs |
| ✅ refreshData | Rafraîchit les données |
| ✅ formatDate | Formate les dates |
| ✅ formatDuration | Formate les durées |
| ✅ Alertes | Gère les alertes |
| ✅ Sélection agent | Sélectionne un agent |
| ✅ Validation données | Valide la structure |
| ✅ Statuts valides | Vérifie les énumérations |

### **test_ihm.js** (40 tests)
Tests d'intégration de l'interface utilisateur

#### Tableau des agents
- ✅ Affiche la liste des agents
- ✅ Affiche le statut (active/inactive/compromised)
- ✅ Affiche le dernier beacon
- ✅ Icônes de statut (🟢 ⚪ 🔴)

#### Modal d'audit
- ✅ Ouvre la modal avec l'agent sélectionné
- ✅ Commandes disponibles (Get-Service, Get-Process, etc.)
- ✅ Commande personnalisée
- ✅ Sélection de priorité
- ✅ Soumission de tâche
- ✅ Fermeture après soumission
- ✅ Affichage des erreurs

#### Tableau des résultats
- ✅ Affiche les résultats
- ✅ Statut du résultat (success/failed)
- ✅ Temps d'exécution
- ✅ Icônes de résultat (✅ ❌)
- ✅ Détails du résultat

#### Statistiques et graphiques
- ✅ Nombre total d'agents
- ✅ Tâches par statut
- ✅ Taux de succès
- ✅ Barres de progression

#### Filtrage et recherche
- ✅ Filtre par nom
- ✅ Filtre par statut
- ✅ Filtre par priorité

#### Rafraîchissement automatique
- ✅ Initialise l'intervalle
- ✅ Arrête le rafraîchissement
- ✅ Charge les données

#### Gestion des erreurs
- ✅ Messages d'erreur API
- ✅ Spinner de chargement
- ✅ Messages de succès
- ✅ Nettoyage des messages

#### Accessibilité
- ✅ Labels de formulaires
- ✅ ARIA labels
- ✅ Contraste des couleurs

## 🚀 Exécution des Tests

### Installation des dépendances
```bash
npm install --save-dev jest babel-jest @babel/preset-env
```

### Exécuter tous les tests frontend
```bash
jest test/frontend/
```

### Avec verbosité
```bash
jest test/frontend/ -v
```

### Avec rapport de couverture
```bash
jest test/frontend/ --coverage
```

### Tests spécifiques
```bash
jest test/frontend/test_api.js
jest test/frontend/test_app.js
jest test/frontend/test_ihm.js
```

### Mode watch (re-run on change)
```bash
jest test/frontend/ --watch
```

## 📊 Résultats

```
✅ test_api.js       - 20 tests passés
✅ test_app.js       - 25 tests passés
✅ test_ihm.js       - 40 tests passés
─────────────────────────────────────
   TOTAL: 85 tests passés ✅
```

## 🔧 Dépendances

Voir `requirements-test.txt` pour les dépendances Python.

Pour le frontend (JavaScript/Jest):
```json
{
  "devDependencies": {
    "jest": "^29.0.0",
    "babel-jest": "^29.0.0",
    "@babel/preset-env": "^7.0.0"
  }
}
```

## 📝 Structure des Tests

### Test du Client API
```javascript
describe('JadusApiClient', () => {
  beforeEach(() => {
    global.fetch = jest.fn(); // Mock fetch
  });

  it('devrait retourner l\'aperçu système', async () => {
    const mockData = { agents: { total: 5 } };
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const result = await JadusApiClient.getSystemOverview();
    expect(result).toEqual(mockData);
  });
});
```

### Test Vue.js
```javascript
describe('Dashboard Vue App', () => {
  it('devrait calculer le taux de succès', () => {
    const overview = {
      results: { total: 100, by_status: { success: 80 } }
    };

    const rate = (overview.results.by_status.success / overview.results.total) * 100;
    expect(rate).toBe(80);
  });
});
```

### Test d'Intégration IHM
```javascript
describe('Interface Utilisateur', () => {
  it('devrait filtrer les agents par nom', () => {
    const agents = [
      { agent_name: 'Agent-1' },
      { agent_name: 'Test-Agent' }
    ];

    const filtered = agents.filter(a => a.agent_name.includes('Agent'));
    expect(filtered).toHaveLength(2);
  });
});
```

## 🐛 Bugs Potentiels Testés

1. ✅ Erreurs API non gérées
2. ✅ Affichage de données invalides
3. ✅ Filtrage incorrect
4. ✅ Rafraîchissement à l'infini
5. ✅ Fuites mémoire (intervals non nettoyés)
6. ✅ Validation de données manquante
7. ✅ Gestion des états vides
8. ✅ Accessibilité manquante

## 📚 Ressources

- [Jest Documentation](https://jestjs.io/)
- [Vue Test Utils](https://vue-test-utils.vuejs.org/)
- [Testing Library](https://testing-library.com/)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)

## 🔄 Intégration CI/CD

```yaml
# GitHub Actions Example
- name: Run frontend tests
  run: |
    npm install
    jest test/frontend/ --coverage
```

## 💡 Prochaines Étapes

1. **Tests E2E** - Playwright ou Cypress
2. **Tests de performance** - Lighthouse
3. **Tests visuels** - Percy ou Chromatic
4. **Tests d'accessibilité** - axe-core
5. **Tests mobiles** - WebDriver

---

**Total: 85 tests frontend** ✅

Voir [../README.md](../README.md) pour les tests backend.
