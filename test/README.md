# Tests Unitaires - Guide d'Exécution

## 📁 Structure des Tests

```
test/
├── __init__.py                 # Initialisation du module test
├── conftest.py                 # Fixtures pytest partagées
├── test_auth.py                # Tests pour l'authentification
├── test_rate_limiter.py        # Tests pour le rate limiting
├── test_models.py              # Tests pour les modèles Pydantic
├── test_database.py            # Tests pour la base de données
└── test_logger.py              # Tests pour le logging
```

## 🚀 Installation des Dépendances

### Avec venv activé:
```bash
pip install -r requirements-test.txt
```

## ▶️ Exécution des Tests

### Exécuter tous les tests:
```bash
pytest
```

### Exécuter les tests avec verbosité:
```bash
pytest -v
```

### Exécuter les tests avec couverture de code:
```bash
pytest --cov=app --cov-report=html
```

### Exécuter un fichier de test spécifique:
```bash
pytest test/test_auth.py
```

### Exécuter une classe de test:
```bash
pytest test/test_database.py::TestDatabaseAgents
```

### Exécuter un test spécifique:
```bash
pytest test/test_auth.py::TestVerifyAgentCredentials::test_valid_credentials
```

### Exécuter avec arrêt à la première erreur:
```bash
pytest -x
```

### Exécuter en mode watch (regénère à chaque changement):
```bash
pytest-watch
```

## 📊 Couverture de Code

Générer un rapport de couverture HTML:
```bash
pytest --cov=app --cov-report=html
```

Le rapport s'ouvre dans `htmlcov/index.html`

## 📝 Fichiers de Test

### **test_auth.py** (7 tests)
- ✅ Vérification de credentials valides
- ✅ Rejet des agent_id invalides
- ✅ Rejet des api_key invalides
- ✅ Rejet des credentials manquantes
- ✅ Sensibilité à la casse

### **test_rate_limiter.py** (11 tests)
- ✅ Première requête acceptée
- ✅ Plusieurs requêtes acceptées
- ✅ Rejet au-delà du limit
- ✅ Isolation par agent
- ✅ Isolation par endpoint
- ✅ Expiration de la fenêtre
- ✅ Récupération des statistiques
- ✅ Réinitialisation du rate limit

### **test_models.py** (15 tests)
- ✅ Validation EnrollRequest
- ✅ Validation BeaconRequest
- ✅ Validation TaskCreateRequest
- ✅ Validation AuditResultRequest (dict et string)
- ✅ Modèles Agent, Task, AuditResult
- ✅ Énumerations AgentStatus et TaskStatus

### **test_database.py** (25 tests)
- ✅ Création d'agents
- ✅ Récupération d'agents
- ✅ Authentification d'agents
- ✅ Création et gestion de tâches
- ✅ Tâches en attente (pending)
- ✅ Assignation de tâches
- ✅ Stockage de résultats
- ✅ Mise à jour des statuts
- ✅ Historique des beacons
- ✅ Workflow complet intégré

### **test_logger.py** (10 tests)
- ✅ Création de loggers
- ✅ Instances multiples
- ✅ Handlers et formatage
- ✅ Niveaux de log
- ✅ Contexte supplémentaire

## 📈 Statistiques

- **Total des tests**: 68 tests
- **Modules couverts**: 5 (auth, rate_limiter, models, database, logger)
- **Couverture attendue**: ~85-90% du code principal

## 🐛 Debugging

### Exécuter un test avec output détaillé:
```bash
pytest -vv -s test/test_auth.py::TestVerifyAgentCredentials::test_valid_credentials
```

### Afficher les variables locales en cas d'erreur:
```bash
pytest -l
```

### Utiliser pdb (debugger Python):
```bash
pytest --pdb test/test_auth.py
```

## ✅ Bonnes Pratiques

1. **Fixtures**: Utilisez les fixtures de `conftest.py` plutôt que de recréer les objets
2. **Nommage**: Les tests suivent le pattern `test_description_behavior`
3. **Isolation**: Chaque test est indépendant (pas de dépendances entre tests)
4. **Assertion**: Utilisez `assert` plutôt que des méthodes de vérification
5. **Contexte**: Les fixtures setup et teardown la base de données automatiquement

## 🔧 Intégration CI/CD

Pour intégrer les tests dans un pipeline CI/CD (GitHub Actions, GitLab CI, etc.):

```yaml
# Example: GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest --cov=app --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## 📚 Ressources

- [Documentation pytest](https://docs.pytest.org/)
- [Pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Coverage.py](https://coverage.readthedocs.io/)
