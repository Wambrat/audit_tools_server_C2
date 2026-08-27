# ðŸš€ Installation Guide - jadus Server with TLS/HTTPS

Ce guide vous accompagne Ã  travers l'installation du jadus Server avec **chiffrement TLS/HTTPS complet**, mÃªme en dÃ©veloppement.

## ðŸ“‹ PrÃ©requis

- **Docker Desktop** (incluant Docker & Docker Compose)
  - TÃ©lÃ©charger: https://www.docker.com/products/docker-desktop
  - VÃ©rifier l'installation:
    ```powershell
    docker --version
    docker-compose --version
    ```
- **OpenSSL** (pour gÃ©nÃ©rer les certificats)
  - Windows: GÃ©nÃ©ralement inclus dans Git Bash ou WSL
  - ou installer via: `choco install openssl`
- **PowerShell 5.1+** (Windows) ou **bash** (Linux/macOS)

## ðŸš€ Quick Start (5 minutes) - Option Automatique

### Windows (PowerShell) - RecommandÃ©

```powershell
# ExÃ©cuter le script d'installation automatique
powershell -ExecutionPolicy Bypass -File .\quick-start.ps1
```

### Linux/macOS (Bash)

```bash
bash ./quick-start.sh
```

**Le script va automatiquement:**
1. âœ“ VÃ©rifier Docker et Docker Compose
2. âœ“ GÃ©nÃ©rer les certificats TLS auto-signÃ©s
3. âœ“ CrÃ©er le fichier `.env`
4. âœ“ Lancer tous les services
5. âœ“ Afficher les logs

---

## ðŸ”§ Installation Manuelle (Si vous prÃ©fÃ©rez)

### Ã‰tape 1: GÃ©nÃ©rer les Certificats TLS

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1
```

**Linux/macOS (Bash):**
```bash
bash ./generate-certs.sh
```

**RÃ©sultat attendu:**
```
âœ… Certificates generated successfully!

ðŸ“ Generated files:
  - ca.pem                  : CA certificate
  - mongodb-combined.pem    : MongoDB cert + key
  - api.pem                 : API/Nginx certificate
  - api-key.pem             : API/Nginx private key
```

### Ã‰tape 2: CrÃ©er la Configuration

```powershell
# Copier le fichier d'exemple
cp .env.example .env

# Ã‰diter les paramÃ¨tres importants
notepad .env
```

**Valeurs Ã  modifier:**
- `MONGO_INITDB_ROOT_PASSWORD` - Changez le mot de passe MongoDB!
- `SECRET_KEY` - ClÃ© secrÃ¨te alÃ©atoire (min. 32 caractÃ¨res)
- `ADMIN_PASSWORD` - Mot de passe administrateur
- `ALLOWED_ORIGINS` - URLs autorisÃ©es (dÃ©jÃ  configurÃ© pour localhost HTTPS)

### Ã‰tape 3: DÃ©marrer les Services

```powershell
# Construire et dÃ©marrer les conteneurs
docker-compose up -d --build

# VÃ©rifier l'Ã©tat des services
docker-compose ps
```

**RÃ©sultat attendu:**
```
NAME              STATUS              PORTS
jadus-traefik        Up (healthy)        0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
jadus-mongodb        Up (healthy)        27017/tcp
jadus-backend        Up (healthy)        0.0.0.0:8000->8000/tcp
jadus-frontend       Up (healthy)        80/tcp
```

### Ã‰tape 4: AccÃ©der aux Services

| Service | URL | Type |
|---------|-----|------|
| **Frontend/Panel** | `https://localhost` | Web UI (HTTPS) |
| **API Swagger Docs** | `https://localhost/api/docs` | Documentation API |
| **Health Check** | `https://localhost/health` | VÃ©rification santÃ© |

### Ã‰tape 5: Premier AccÃ¨s

1. AccÃ©der Ã  `https://localhost`
2. Le navigateur affiche un avertissement (normal, certificat auto-signÃ©)
3. Cliquer sur **"Continuer malgrÃ© tout"** / **"Proceed"**
4. Se connecter avec:
   - Identifiant: `admin`
   - Mot de passe: Celui dÃ©fini dans `.env` (`ADMIN_PASSWORD`)

## ðŸ” Architecture TLS

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Navigateur (HTTPS)           â”‚
â”‚   https://localhost            â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
             â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   Traefik (Reverse Proxy)      â”‚
â”‚   - Ã‰coute ports 80/443        â”‚
â”‚   - Certificat TLS: api.pem    â”‚
â”‚   - Redirige HTTP â†’ HTTPS      â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
    â†™            â†™            â†˜
Frontend      Backend      MongoDB
(Nginx)      (FastAPI)      (TLS)
Port 80      Port 8000    Port 27017
```

## ðŸ” Certificat Auto-SignÃ©

Lors du premier accÃ¨s Ã  `https://localhost`, le navigateur affiche un avertissement.

### Chrome/Edge
1. Cliquer sur **"DÃ©tails"** / **"Advanced"**
2. Cliquer sur **"Continuer vers localhost"** / **"Proceed"**

### Firefox
- Cliquer sur **"Accepter le risque et continuer"**

### Pour Ã©viter les avertissements (optionnel):
```powershell
# Importer le CA dans Windows
certutil -addstore -f 'Root' .\certs\ca.pem
```

## ðŸŽ›ï¸ Commandes Utiles

### Gestion des Services

```powershell
# DÃ©marrer les services
docker-compose up -d

# Afficher l'Ã©tat
docker-compose ps

# Voir les logs
docker-compose logs -f

# Logs d'un service spÃ©cifique
docker-compose logs -f backend

# RedÃ©marrer un service
docker-compose restart backend

# ArrÃªter complÃ¨tement (donnÃ©es preservÃ©es)
docker-compose down

# ArrÃªter et supprimer tout (y compris donnÃ©es!)
docker-compose down -v

# Reconstruire les images
docker-compose build
```

### AccÃ¨s Ã  la Base de DonnÃ©es

```powershell
# Shell MongoDB interactif
docker-compose exec mongodb mongosh --tlsMode preferTLS --tlsCAFile /etc/mongodb/ca.pem

# Lister les bases de donnÃ©es
> show dbs

# Utiliser jadus_server_db
> use jadus_server_db

# Afficher les collections
> show collections

# Quitter
> exit
```

### VÃ©rifier le Chiffrement

```powershell
# Afficher le certificat TLS
openssl x509 -in ./certs/api.pem -text -noout

# VÃ©rifier la connexion HTTPS
openssl s_client -connect localhost:443 -servername localhost

# Tester l'API
curl -k https://localhost/health

# Avec headers dÃ©taillÃ©s
curl -k -i https://localhost/health
```

## âš ï¸ DÃ©pannage

### Erreur: "Certificate Verification Failed"

**Cause:** Certificat auto-signÃ© non approuvÃ© par le navigateur

**Solution:**
- Accepter le certificat dans le navigateur (voir "Certificat Auto-SignÃ©" ci-dessus)
- Importer le CA en tant qu'autoritÃ© de confiance
- Pour les outils (curl): ajouter `-k`
  ```powershell
  curl -k https://localhost/health
  ```

### "Port 80 already in use"

```powershell
# Trouver le processus utilisant le port
netstat -ano | findstr :80

# ArrÃªter le processus (remplacer PID)
taskkill /PID <PID> /F

# Ou utiliser un port diffÃ©rent dans docker-compose.yml
```

### MongoDB Connection Fails

**VÃ©rifications:**
```powershell
# 1. Certificats existent
Test-Path ./certs/mongodb-combined.pem

# 2. Les mots de passe correspondent
# VÃ©rifier dans .env:
# MONGO_INITDB_ROOT_PASSWORD doit correspondre Ã  celui dans MONGODB_URI

# 3. RedÃ©marrer MongoDB
docker-compose restart mongodb

# 4. Voir les logs
docker-compose logs mongodb
```

### Services ne dÃ©marrent pas

```powershell
# Voir tous les logs
docker-compose logs

# VÃ©rifier les ressources disponibles
docker stats

# RedÃ©marrer complÃ¨tement
docker-compose down
docker system prune -f
docker-compose up -d --build
```

### Traefik n'expose pas les routes

```powershell
# VÃ©rifier les logs Traefik
docker-compose logs traefik

# VÃ©rifier que les certificats sont montÃ©s
docker exec jadus-traefik ls -la /etc/traefik/certs/

# RedÃ©marrer
docker-compose restart traefik
```

### Login Admin Ã©choue

**VÃ©rifications:**
1. Identifiant: doit Ãªtre `admin` ou `ADMIN_USERNAME` de `.env`
2. Mot de passe: doit correspondre Ã  `ADMIN_PASSWORD` de `.env`
3. Lire les logs: `docker-compose logs backend`

## ðŸ“ˆ Renouveler les Certificats

Les certificats durent **365 jours** par dÃ©faut.

```powershell
# 1. Supprimer les anciens
Remove-Item ./certs -Recurse -Force

# 2. RegÃ©nÃ©rer
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1

# 3. RedÃ©marrer les services
docker-compose restart traefik mongodb backend
```

## ðŸ“š Documentation AvancÃ©e

- **[TLS_SETUP.md](./TLS_SETUP.md)** - Configuration TLS dÃ©taillÃ©e et avancÃ©e
- **[README.md](./README.md)** - Vue d'ensemble du projet
- **[docs/api/API.md](./docs/api/API.md)** - Documentation API complÃ¨te

