# 📚 Documentation Jadus Audit

Bienvenue dans la documentation du système de gestion Jadus Audit!

## 🚀 Pour Commencer

**Nouveau sur le projet?** Commencez par:
- 👉 [Guide Rapide - 5 minutes](setup/QUICK_START.md)
- 🔧 [MongoDB - Configuration Production](setup/MONGODB.md)

---

## 📖 Index Complet

### 🟢 **Setup & Démarrage**

- **[Quick Start](setup/QUICK_START.md)** - Démarrer en 5 minutes
  - Installation
  - Configuration basique
  - Lancer le dashboard
  - Premiers audits

- **[MongoDB](setup/MONGODB.md)** - Production Database
  - Configuration MongoDB
  - Migration mémoire → MongoDB
  - Backup & Restore
  - Performance & HA

---

### 📡 **API & Intégration**

- **[API Documentation](api/API.md)** - Endpoints & Authentification
  - Architecture des endpoints
  - Authentification JWT pour admin
  - Rate limiting
  - Exemples d'utilisation
  - Codes de réponse

---

### 🏗️ **Architecture & Sécurité**

- **[Architecture](architecture/ARCHITECTURE.md)** - Design Global du Système
  - Composants
  - Flux de données
  - Database schema
  - Monitoring

- **[Sécurité](architecture/SECURITY.md)** - Phase 5 Security Hardening
  - SQL Injection Prevention (59 tests)
  - CORS Security (45 tests)
  - Session Management & Key Rotation (29 tests)
  - Encryption Key Management
  - Audit Logging
  - CSRF Protection
  - Security Headers
  - XSS Prevention

---

### 🧪 **Tests & Validation**

- **[Testing Guide](testing/TESTING.md)** - Stratégie & Guides de Test
  - Unit tests (376 tests passants)
  - Integration tests
  - Backend API tests
  - Frontend tests
  - Exécution des tests
  - CI/CD

- **[Test Summary](testing/TEST_SUMMARY.md)** - Résumé des Résultats
  - Couverture
  - Statistiques
  - Résultats Phase 5

- **[Frontend Tests](testing/FRONTEND_TESTS.md)** - Tests du Dashboard
  - Jest tests
  - UI testing
  - Performance tests

---

## 🎯 Guides par Rôle

### 👨‍💼 **Administrateur**

Vous gérez le système Jadus Audit:
1. Lire: [Quick Start](setup/QUICK_START.md)
2. Lire: [API Documentation](api/API.md) - Section "Admin Operations"
3. Consulter: [Architecture](architecture/ARCHITECTURE.md) - Dashboard & Monitoring

**Tâches courantes:**
- Lancer le serveur: `python main.py`
- Accéder au dashboard: `http://localhost:8000/docs`
- Enregistrer des agents PowerShell
- Voir les alertes et les statistiques

---

### 👨‍💻 **Développeur Backend**

Vous développez ou intégrez l'API:
1. Lire: [Architecture](architecture/ARCHITECTURE.md)
2. Lire: [API Documentation](api/API.md)
3. Consulter: [Sécurité](architecture/SECURITY.md) - Vérifications obligatoires
4. Lancer les tests: [Testing Guide](testing/TESTING.md)

**Fichiers clés:**
- `main.py` - Initialisation FastAPI
- `app/routes.py` - Endpoints
- `app/models.py` - Pydantic models
- `test/` - Tests unitaires

---

### 🔐 **DevSecOps**

Vous maintenez la sécurité:
1. Lire: [Sécurité](architecture/SECURITY.md) - **Impératif!**
2. Lire: [MongoDB](setup/MONGODB.md) - Configuration sécurisée
3. Consulter: [API Documentation](api/API.md) - JWT & Authentification

**Points de contrôle:**
- ✅ 376 tests de sécurité passants
- ✅ Encryption key rotation
- ✅ SQL injection prevention
- ✅ CORS security
- ✅ Rate limiting
- ✅ Audit logging

---

### 🧪 **QA/Testeur**

Vous testez le système:
1. Lire: [Testing Guide](testing/TESTING.md)
2. Consulter: [Quick Start](setup/QUICK_START.md) - Setup
3. Lire: [Architecture](architecture/ARCHITECTURE.md) - Composants à tester

**Commandes:**
```bash
# Tous les tests
python -m pytest test/ -v

# Tests spécifiques
python -m pytest test/test_sql_injection_prevention.py -v

# Coverage
python -m pytest test/ --cov=app --cov-report=html
```

---

## 📊 Statistiques du Projet

| Métrique | Valeur |
|----------|--------|
| **Tests Unitaires** | 376/376 ✅ |
| **Tests de Sécurité** | 133 |
| **SQL Injection Tests** | 59 |
| **CORS Tests** | 45 |
| **Session Management Tests** | 29 |
| **Code Coverage** | >95% |
| **Endpoints API** | 15+ |
| **Database Modes** | 2 (Memory, MongoDB) |
| **Auth Systems** | 3 (Agent, Admin JWT, Rate Limit) |

---

## 🚨 Important - Sécurité

⚠️ **Avant de déployer en production:**

1. ✅ Lire [Sécurité](architecture/SECURITY.md) complètement
2. ✅ Vérifier `.env` - Secrets configurés (voir `ENCRYPTION_KEY`, `CSRF_SECRET_KEY`, `ADMIN_SECRET_KEY`)
3. ✅ Configurer MongoDB avec authentification
4. ✅ Activer HTTPS en production
5. ✅ Vérifier les CORS - Uniquement les origines autorisées
6. ✅ Mettre en place les backups
7. ✅ Configurer la rotation des logs
8. ✅ Utiliser JWT tokens avec expiration courte
9. ✅ Auditer les accès administrateur
10. ✅ Tester les scenarios de sécurité (voir [Tests](testing/TESTING.md))

---

## 🔗 Ressources Externes

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [OWASP Security Guidelines](https://owasp.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

---

## 📞 Support & Issues

**En cas de problème:**

1. Consulter la doc pertinente (voir index ci-dessus)
2. Vérifier les logs: `tail -f logs/c2_server.log`
3. Lancer les tests: `python -m pytest test/ -v`
4. Vérifier MongoDB: `mongosh` → `db.serverStatus()`
5. Vérifier l'API: `curl http://localhost:8000/health`

---

## 📄 Fichiers de Configuration

| Fichier | Rôle |
|---------|------|
| `.env` | Variables d'environnement |
| `requirements.txt` | Dépendances Python |
| `pytest.ini` | Configuration tests |
| `main.py` | Point d'entrée API |
| `docker-compose.yml` | Stack Docker (optionnel) |

---

## 🎯 Prochaines Étapes

- ✅ Lire [Quick Start](setup/QUICK_START.md)
- ✅ Lancer `python main.py`
- ✅ Accéder au dashboard
- ✅ Enregistrer un agent
- ✅ Lancer un audit
- ✅ Consulter la doc selon vos besoins

**Bienvenue dans le Jadus Audit!** 🚀
