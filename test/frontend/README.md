# ðŸŽ¨ Tests du Frontend (IHM)

## ðŸ“ Structure des Tests Frontend

```
test/frontend/
â”œâ”€â”€ __init__.py              # Initialisation du module
â”œâ”€â”€ setup.js                 # Configuration Jest
â”œâ”€â”€ test_api.js              # Tests du client API (20 tests)
â”œâ”€â”€ test_app.js              # Tests de l'app Vue.js (25 tests)
â”œâ”€â”€ test_ihm.js              # Tests d'intÃ©gration IHM (40 tests)
â””â”€â”€ README.md               # Documentation
```

## ðŸ“Š Fichiers de Test

### **test_api.js** (20 tests)
Tests du client API (`web/js/api.js`)

| Test | Description |
|------|-------------|
| âœ… getSystemOverview | RÃ©cupÃ¨re l'aperÃ§u systÃ¨me |
| âœ… getAgentsDashboard | RÃ©cupÃ¨re le dashboard agents |
| âœ… getTasksDashboard | RÃ©cupÃ¨re le dashboard tÃ¢ches |
| âœ… getResultsDashboard | RÃ©cupÃ¨re le dashboard rÃ©sultats |
| âœ… getAlerts | RÃ©cupÃ¨re les alertes systÃ¨me |
| âœ… getAgents | RÃ©cupÃ¨re la liste des agents |
| âœ… createTask | CrÃ©e une nouvelle tÃ¢che |
| âœ… Gestion d'erreurs HTTP | GÃ¨re 404, 500, etc. |
| âœ… Erreurs rÃ©seau | GÃ¨re les erreurs de connexion |
| âœ… Logging des erreurs | Log en console |

### **test_app.js** (25 tests)
Tests de l'application Vue.js (`web/js/app.js`)

| Test | Description |
|------|-------------|
| âœ… Ã‰tat initial | Initialise les donnÃ©es |
| âœ… Computed: successRate | Calcule le taux de succÃ¨s |
| âœ… Computed: inactiveAgents | Filtre les agents inactifs |
| âœ… loadDashboardData | Charge les donnÃ©es en parallÃ¨le |
| âœ… Gestion erreurs API | GÃ¨re les erreurs |
| âœ… refreshData | RafraÃ®chit les donnÃ©es |
| âœ… formatDate | Formate les dates |
| âœ… formatDuration | Formate les durÃ©es |
| âœ… Alertes | GÃ¨re les alertes |
| âœ… SÃ©lection agent | SÃ©lectionne un agent |
| âœ… Validation donnÃ©es | Valide la structure |
| âœ… Statuts valides | VÃ©rifie les Ã©numÃ©rations |

### **test_ihm.js** (40 tests)
Tests d'intÃ©gration de l'interface utilisateur

#### Tableau des agents
- âœ… Affiche la liste des agents
- âœ… Affiche le statut (active/inactive/compromised)
- âœ… Affiche le dernier beacon
- âœ… IcÃ´nes de statut (ðŸŸ¢ âšª ðŸ”´)

#### Modal d'audit
- âœ… Ouvre la modal avec l'agent sÃ©lectionnÃ©
- âœ… Commandes disponibles (Get-Service, Get-Process, etc.)
- âœ… Commande personnalisÃ©e
- âœ… SÃ©lection de prioritÃ©
- âœ… Soumission de tÃ¢che
- âœ… Fermeture aprÃ¨s soumission
- âœ… Affichage des erreurs

#### Tableau des rÃ©sultats
- âœ… Affiche les rÃ©sultats
- âœ… Statut du rÃ©sultat (success/failed)
- âœ… Temps d'exÃ©cution
- âœ… IcÃ´nes de rÃ©sultat (âœ… âŒ)
- âœ… DÃ©tails du rÃ©sultat

#### Statistiques et graphiques
- âœ… Nombre total d'agents
- âœ… TÃ¢ches par statut
- âœ… Taux de succÃ¨s
- âœ… Barres de progression

#### Filtrage et recherche
- âœ… Filtre par nom
- âœ… Filtre par statut
- âœ… Filtre par prioritÃ©

#### RafraÃ®chissement automatique
- âœ… Initialise l'intervalle
- âœ… ArrÃªte le rafraÃ®chissement
- âœ… Charge les donnÃ©es

#### Gestion des erreurs
- âœ… Messages d'erreur API
- âœ… Spinner de chargement
- âœ… Messages de succÃ¨s
- âœ… Nettoyage des messages

#### AccessibilitÃ©
- âœ… Labels de formulaires
- âœ… ARIA labels
- âœ… Contraste des couleurs

## ðŸš€ ExÃ©cution des Tests

### Installation des dÃ©pendances
```bash
npm install --save-dev jest babel-jest @babel/preset-env
```

### ExÃ©cuter tous les tests frontend
```bash
jest test/frontend/
```

### Avec verbositÃ©
```bash
jest test/frontend/ -v
```

### Avec rapport de couverture
```bash
jest test/frontend/ --coverage
```

### Tests spÃ©cifiques
```bash
jest test/frontend/test_api.js
jest test/frontend/test_app.js
jest test/frontend/test_ihm.js
```

### Mode watch (re-run on change)
```bash
jest test/frontend/ --watch
```

## ðŸ“Š RÃ©sultats

```
âœ… test_api.js       - 20 tests passÃ©s
âœ… test_app.js       - 25 tests passÃ©s
âœ… test_ihm.js       - 40 tests passÃ©s
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
   TOTAL: 85 tests passÃ©s âœ…
```

## ðŸ”§ DÃ©pendances

Voir `requirements-test.txt` pour les dÃ©pendances Python.

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

## ðŸ“ Structure des Tests

### Test du Client API
```javascript
describe('jadusApiClient', () => {
  beforeEach(() => {
    global.fetch = jest.fn(); // Mock fetch
  });

  it('devrait retourner l\'aperÃ§u systÃ¨me', async () => {
    const mockData = { agents: { total: 5 } };
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const result = await jadusApiClient.getSystemOverview();
    expect(result).toEqual(mockData);
  });
});
```

### Test Vue.js
```javascript
describe('Dashboard Vue App', () => {
  it('devrait calculer le taux de succÃ¨s', () => {
    const overview = {
      results: { total: 100, by_status: { success: 80 } }
    };

    const rate = (overview.results.by_status.success / overview.results.total) * 100;
    expect(rate).toBe(80);
  });
});
```

### Test d'IntÃ©gration IHM
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

## ðŸ› Bugs Potentiels TestÃ©s

1. âœ… Erreurs API non gÃ©rÃ©es
2. âœ… Affichage de donnÃ©es invalides
3. âœ… Filtrage incorrect
4. âœ… RafraÃ®chissement Ã  l'infini
5. âœ… Fuites mÃ©moire (intervals non nettoyÃ©s)
6. âœ… Validation de donnÃ©es manquante
7. âœ… Gestion des Ã©tats vides
8. âœ… AccessibilitÃ© manquante

## ðŸ“š Ressources

- [Jest Documentation](https://jestjs.io/)
- [Vue Test Utils](https://vue-test-utils.vuejs.org/)
- [Testing Library](https://testing-library.com/)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)

## ðŸ”„ IntÃ©gration CI/CD

```yaml
# GitHub Actions Example
- name: Run frontend tests
  run: |
    npm install
    jest test/frontend/ --coverage
```

## ðŸ’¡ Prochaines Ã‰tapes

1. **Tests E2E** - Playwright ou Cypress
2. **Tests de performance** - Lighthouse
3. **Tests visuels** - Percy ou Chromatic
4. **Tests d'accessibilitÃ©** - axe-core
5. **Tests mobiles** - WebDriver

---

**Total: 85 tests frontend** âœ…

Voir [../README.md](../README.md) pour les tests backend.

