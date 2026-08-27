# ðŸ“š Documentation jadus Server

Bienvenue dans la documentation du systÃ¨me de gestion jadus!

## ðŸš€ Pour Commencer

**Nouveau sur le projet?** Commencez par:
- ðŸ‘‰ [Guide Rapide - 5 minutes](setup/QUICK_START.md)
- ðŸ”§ [MongoDB - Configuration Production](setup/MONGODB.md)

---

## ðŸ“– Index Complet

### ðŸŸ¢ **Setup & DÃ©marrage**

- **[Quick Start](setup/QUICK_START.md)** - DÃ©marrer en 5 minutes
  - Installation
  - Configuration basique
  - Lancer le dashboard
  - Premiers audits

- **[MongoDB](setup/MONGODB.md)** - Production Database
  - Configuration MongoDB
  - Migration mÃ©moire â†’ MongoDB
  - Backup & Restore
  - Performance & HA

---

### ðŸ“¡ **API & IntÃ©gration**

- **[API Documentation](api/API.md)** - Endpoints & Authentification
  - Architecture des endpoints
  - Authentification JWT pour admin
  - Rate limiting
  - Exemples d'utilisation
  - Codes de rÃ©ponse

---

### ðŸ—ï¸ **Architecture & SÃ©curitÃ©**

- **[Architecture](architecture/ARCHITECTURE.md)** - Design Global du SystÃ¨me
  - Composants
  - Flux de donnÃ©es
  - Database schema
  - Monitoring

- **[SÃ©curitÃ©](architecture/SECURITY.md)** - Phase 5 Security Hardening
  - SQL Injection Prevention (59 tests)
  - CORS Security (45 tests)
  - Session Management & Key Rotation (29 tests)
  - Encryption Key Management
  - Audit Logging
  - CSRF Protection
  - Security Headers
  - XSS Prevention

---

### ðŸ§ª **Tests & Validation**

- **[Testing Guide](testing/TESTING.md)** - StratÃ©gie & Guides de Test
  - Unit tests (376 tests passants)
  - Integration tests
  - Backend API tests
  - Frontend tests
  - ExÃ©cution des tests
  - CI/CD

- **[Test Summary](testing/TEST_SUMMARY.md)** - RÃ©sumÃ© des RÃ©sultats
  - Couverture
  - Statistiques
  - RÃ©sultats Phase 5

- **[Frontend Tests](testing/FRONTEND_TESTS.md)** - Tests du Dashboard
  - Jest tests
  - UI testing
  - Performance tests

---

## ðŸŽ¯ Guides par RÃ´le

### ðŸ‘¨â€ðŸ’¼ **Administrateur**

Vous gÃ©rez le systÃ¨me jadus:
1. Lire: [Quick Start](setup/QUICK_START.md)
2. Lire: [API Documentation](api/API.md) - Section "Admin Operations"
3. Consulter: [Architecture](architecture/ARCHITECTURE.md) - Dashboard & Monitoring

**TÃ¢ches courantes:**
- Lancer le serveur: `python main.py`
- AccÃ©der au dashboard: `http://localhost:8000/docs`
- Enregistrer des agents PowerShell
- Voir les alertes et les statistiques

---

### ðŸ‘¨â€ðŸ’» **DÃ©veloppeur Backend**

Vous dÃ©veloppez ou intÃ©grez l'API:
1. Lire: [Architecture](architecture/ARCHITECTURE.md)
2. Lire: [API Documentation](api/API.md)
3. Consulter: [SÃ©curitÃ©](architecture/SECURITY.md) - VÃ©rifications obligatoires
4. Lancer les tests: [Testing Guide](testing/TESTING.md)

**Fichiers clÃ©s:**
- `main.py` - Initialisation FastAPI
- `app/routes.py` - Endpoints
- `app/models.py` - Pydantic models
- `test/` - Tests unitaires

---

### ðŸ” **DevSecOps**

Vous maintenez la sÃ©curitÃ©:
1. Lire: [SÃ©curitÃ©](architecture/SECURITY.md) - **ImpÃ©ratif!**
2. Lire: [MongoDB](setup/MONGODB.md) - Configuration sÃ©curisÃ©e
3. Consulter: [API Documentation](api/API.md) - JWT & Authentification

**Points de contrÃ´le:**
- âœ… 376 tests de sÃ©curitÃ© passants
- âœ… Encryption key rotation
- âœ… SQL injection prevention
- âœ… CORS security
- âœ… Rate limiting
- âœ… Audit logging

---

### ðŸ§ª **QA/Testeur**

Vous testez le systÃ¨me:
1. Lire: [Testing Guide](testing/TESTING.md)
2. Consulter: [Quick Start](setup/QUICK_START.md) - Setup
3. Lire: [Architecture](architecture/ARCHITECTURE.md) - Composants Ã  tester

**Commandes:**
```bash
# Tous les tests
python -m pytest test/ -v

# Tests spÃ©cifiques
python -m pytest test/test_sql_injection_prevention.py -v

# Coverage
python -m pytest test/ --cov=app --cov-report=html
```

---

## ðŸ“Š Statistiques du Projet

| MÃ©trique | Valeur |
|----------|--------|
| **Tests Unitaires** | 376/376 âœ… |
| **Tests de SÃ©curitÃ©** | 133 |
| **SQL Injection Tests** | 59 |
| **CORS Tests** | 45 |
| **Session Management Tests** | 29 |
| **Code Coverage** | >95% |
| **Endpoints API** | 15+ |
| **Database Modes** | 2 (Memory, MongoDB) |
| **Auth Systems** | 3 (Agent, Admin JWT, Rate Limit) |

---

## ðŸš¨ Important - SÃ©curitÃ©

âš ï¸ **Avant de dÃ©ployer en production:**

1. âœ… Lire [SÃ©curitÃ©](architecture/SECURITY.md) complÃ¨tement
2. âœ… VÃ©rifier `.env` - Secrets configurÃ©s (voir `ENCRYPTION_KEY`, `CSRF_SECRET_KEY`, `ADMIN_SECRET_KEY`)
3. âœ… Configurer MongoDB avec authentification
4. âœ… Activer HTTPS en production
5. âœ… VÃ©rifier les CORS - Uniquement les origines autorisÃ©es
6. âœ… Mettre en place les backups
7. âœ… Configurer la rotation des logs
8. âœ… Utiliser JWT tokens avec expiration courte
9. âœ… Auditer les accÃ¨s administrateur
10. âœ… Tester les scenarios de sÃ©curitÃ© (voir [Tests](testing/TESTING.md))

---

## ðŸ”— Ressources Externes

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [OWASP Security Guidelines](https://owasp.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)

---

## ðŸ“ž Support & Issues

**En cas de problÃ¨me:**

1. Consulter la doc pertinente (voir index ci-dessus)
2. VÃ©rifier les logs: `tail -f logs/jadus_server.log`
3. Lancer les tests: `python -m pytest test/ -v`
4. VÃ©rifier MongoDB: `mongosh` â†’ `db.serverStatus()`
5. VÃ©rifier l'API: `curl http://localhost:8000/health`

---

## ðŸ“„ Fichiers de Configuration

| Fichier | RÃ´le |
|---------|------|
| `.env` | Variables d'environnement |
| `requirements.txt` | DÃ©pendances Python |
| `pytest.ini` | Configuration tests |
| `main.py` | Point d'entrÃ©e API |
| `docker-compose.yml` | Stack Docker (optionnel) |

---

## ðŸŽ¯ Prochaines Ã‰tapes

- âœ… Lire [Quick Start](setup/QUICK_START.md)
- âœ… Lancer `python main.py`
- âœ… AccÃ©der au dashboard
- âœ… Enregistrer un agent
- âœ… Lancer un audit
- âœ… Consulter la doc selon vos besoins

**Bienvenue dans le jadus Server!** ðŸš€

