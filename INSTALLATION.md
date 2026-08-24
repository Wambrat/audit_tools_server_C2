# 🚀 Installation Guide - C2 Server with TLS/HTTPS

Ce guide vous accompagne à travers l'installation du C2 Server avec **chiffrement TLS/HTTPS complet**, même en développement.

## 📋 Prérequis

- **Docker Desktop** (incluant Docker & Docker Compose)
  - Télécharger: https://www.docker.com/products/docker-desktop
  - Vérifier l'installation:
    ```powershell
    docker --version
    docker-compose --version
    ```
- **OpenSSL** (pour générer les certificats)
  - Windows: Généralement inclus dans Git Bash ou WSL
  - ou installer via: `choco install openssl`
- **PowerShell 5.1+** (Windows) ou **bash** (Linux/macOS)

## 🚀 Quick Start (5 minutes) - Option Automatique

### Windows (PowerShell) - Recommandé

```powershell
# Exécuter le script d'installation automatique
powershell -ExecutionPolicy Bypass -File .\quick-start.ps1
```

### Linux/macOS (Bash)

```bash
bash ./quick-start.sh
```

**Le script va automatiquement:**
1. ✓ Vérifier Docker et Docker Compose
2. ✓ Générer les certificats TLS auto-signés
3. ✓ Créer le fichier `.env`
4. ✓ Lancer tous les services
5. ✓ Afficher les logs

---

## 🔧 Installation Manuelle (Si vous préférez)

### Étape 1: Générer les Certificats TLS

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1
```

**Linux/macOS (Bash):**
```bash
bash ./generate-certs.sh
```

**Résultat attendu:**
```
✅ Certificates generated successfully!

📁 Generated files:
  - ca.pem                  : CA certificate
  - mongodb-combined.pem    : MongoDB cert + key
  - api.pem                 : API/Nginx certificate
  - api-key.pem             : API/Nginx private key
```

### Étape 2: Créer la Configuration

```powershell
# Copier le fichier d'exemple
cp .env.example .env

# Éditer les paramètres importants
notepad .env
```

**Valeurs à modifier:**
- `MONGO_INITDB_ROOT_PASSWORD` - Changez le mot de passe MongoDB!
- `SECRET_KEY` - Clé secrète aléatoire (min. 32 caractères)
- `ADMIN_PASSWORD` - Mot de passe administrateur
- `ALLOWED_ORIGINS` - URLs autorisées (déjà configuré pour localhost HTTPS)

### Étape 3: Démarrer les Services

```powershell
# Construire et démarrer les conteneurs
docker-compose up -d --build

# Vérifier l'état des services
docker-compose ps
```

**Résultat attendu:**
```
NAME              STATUS              PORTS
c2-traefik        Up (healthy)        0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
c2-mongodb        Up (healthy)        27017/tcp
c2-backend        Up (healthy)        0.0.0.0:8000->8000/tcp
c2-frontend       Up (healthy)        80/tcp
```

### Étape 4: Accéder aux Services

| Service | URL | Type |
|---------|-----|------|
| **Frontend/Panel** | `https://localhost` | Web UI (HTTPS) |
| **API Swagger Docs** | `https://localhost/api/docs` | Documentation API |
| **Health Check** | `https://localhost/health` | Vérification santé |

### Étape 5: Premier Accès

1. Accéder à `https://localhost`
2. Le navigateur affiche un avertissement (normal, certificat auto-signé)
3. Cliquer sur **"Continuer malgré tout"** / **"Proceed"**
4. Se connecter avec:
   - Identifiant: `admin`
   - Mot de passe: Celui défini dans `.env` (`ADMIN_PASSWORD`)

## 🔐 Architecture TLS

```
┌────────────────────────────────┐
│   Navigateur (HTTPS)           │
│   https://localhost            │
└────────────────────────────────┘
             ↓
┌────────────────────────────────┐
│   Traefik (Reverse Proxy)      │
│   - Écoute ports 80/443        │
│   - Certificat TLS: api.pem    │
│   - Redirige HTTP → HTTPS      │
└────────────────────────────────┘
    ↙            ↙            ↘
Frontend      Backend      MongoDB
(Nginx)      (FastAPI)      (TLS)
Port 80      Port 8000    Port 27017
```

## 🔐 Certificat Auto-Signé

Lors du premier accès à `https://localhost`, le navigateur affiche un avertissement.

### Chrome/Edge
1. Cliquer sur **"Détails"** / **"Advanced"**
2. Cliquer sur **"Continuer vers localhost"** / **"Proceed"**

### Firefox
- Cliquer sur **"Accepter le risque et continuer"**

### Pour éviter les avertissements (optionnel):
```powershell
# Importer le CA dans Windows
certutil -addstore -f 'Root' .\certs\ca.pem
```

## 🎛️ Commandes Utiles

### Gestion des Services

```powershell
# Démarrer les services
docker-compose up -d

# Afficher l'état
docker-compose ps

# Voir les logs
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f backend

# Redémarrer un service
docker-compose restart backend

# Arrêter complètement (données preservées)
docker-compose down

# Arrêter et supprimer tout (y compris données!)
docker-compose down -v

# Reconstruire les images
docker-compose build
```

### Accès à la Base de Données

```powershell
# Shell MongoDB interactif
docker-compose exec mongodb mongosh --tlsMode preferTLS --tlsCAFile /etc/mongodb/ca.pem

# Lister les bases de données
> show dbs

# Utiliser c2_server_db
> use c2_server_db

# Afficher les collections
> show collections

# Quitter
> exit
```

### Vérifier le Chiffrement

```powershell
# Afficher le certificat TLS
openssl x509 -in ./certs/api.pem -text -noout

# Vérifier la connexion HTTPS
openssl s_client -connect localhost:443 -servername localhost

# Tester l'API
curl -k https://localhost/health

# Avec headers détaillés
curl -k -i https://localhost/health
```

## ⚠️ Dépannage

### Erreur: "Certificate Verification Failed"

**Cause:** Certificat auto-signé non approuvé par le navigateur

**Solution:**
- Accepter le certificat dans le navigateur (voir "Certificat Auto-Signé" ci-dessus)
- Importer le CA en tant qu'autorité de confiance
- Pour les outils (curl): ajouter `-k`
  ```powershell
  curl -k https://localhost/health
  ```

### "Port 80 already in use"

```powershell
# Trouver le processus utilisant le port
netstat -ano | findstr :80

# Arrêter le processus (remplacer PID)
taskkill /PID <PID> /F

# Ou utiliser un port différent dans docker-compose.yml
```

### MongoDB Connection Fails

**Vérifications:**
```powershell
# 1. Certificats existent
Test-Path ./certs/mongodb-combined.pem

# 2. Les mots de passe correspondent
# Vérifier dans .env:
# MONGO_INITDB_ROOT_PASSWORD doit correspondre à celui dans MONGODB_URI

# 3. Redémarrer MongoDB
docker-compose restart mongodb

# 4. Voir les logs
docker-compose logs mongodb
```

### Services ne démarrent pas

```powershell
# Voir tous les logs
docker-compose logs

# Vérifier les ressources disponibles
docker stats

# Redémarrer complètement
docker-compose down
docker system prune -f
docker-compose up -d --build
```

### Traefik n'expose pas les routes

```powershell
# Vérifier les logs Traefik
docker-compose logs traefik

# Vérifier que les certificats sont montés
docker exec c2-traefik ls -la /etc/traefik/certs/

# Redémarrer
docker-compose restart traefik
```

### Login Admin échoue

**Vérifications:**
1. Identifiant: doit être `admin` ou `ADMIN_USERNAME` de `.env`
2. Mot de passe: doit correspondre à `ADMIN_PASSWORD` de `.env`
3. Lire les logs: `docker-compose logs backend`

## 📈 Renouveler les Certificats

Les certificats durent **365 jours** par défaut.

```powershell
# 1. Supprimer les anciens
Remove-Item ./certs -Recurse -Force

# 2. Regénérer
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1

# 3. Redémarrer les services
docker-compose restart traefik mongodb backend
```

## 📚 Documentation Avancée

- **[TLS_SETUP.md](./TLS_SETUP.md)** - Configuration TLS détaillée et avancée
- **[README.md](./README.md)** - Vue d'ensemble du projet
- **[docs/api/API.md](./docs/api/API.md)** - Documentation API complète
