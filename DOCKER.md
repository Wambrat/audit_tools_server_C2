# Guide Docker pour l'Application jadus Server

Ce guide explique comment utiliser les images Docker pour dÃ©ployer l'application jadus Server complÃ¨te avec le backend, MongoDB et le frontend.

## ðŸ“‹ PrÃ©requis

- Docker (version 20.10 ou supÃ©rieure)
- Docker Compose (version 1.29 ou supÃ©rieure)
- Au minimum 2GB de RAM disponible

## ðŸš€ DÃ©marrage rapide

### 1. Configuration de l'environnement

Avant de dÃ©marrer, crÃ©ez un fichier `.env` Ã  la racine du projet :

```bash
cp .env.example .env
```

Ã‰ditez le fichier `.env` et mettez Ã  jour les valeurs sensibles :
- `MONGO_INITDB_ROOT_PASSWORD`: Changez le mot de passe MongoDB
- `SECRET_KEY`: GÃ©nÃ©rez une clÃ© secrÃ¨te pour JWT
- `CORS_ORIGINS`: Ajoutez vos domaines autorisÃ©s

### 2. Lancer l'application

```bash
docker-compose up -d
```

Cela va :
- CrÃ©er et dÃ©marrer le conteneur MongoDB
- CrÃ©er et dÃ©marrer le conteneur backend FastAPI
- CrÃ©er et dÃ©marrer le conteneur frontend Nginx

### 3. VÃ©rifier que tout fonctionne

```bash
# VÃ©rifier l'Ã©tat des conteneurs
docker-compose ps

# Consulter les logs
docker-compose logs -f

# Tester l'API backend
curl http://localhost:8000/health

# Tester le frontend
curl http://localhost/health
```

## ðŸ“ AccÃ¨s aux services

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost | Interface web (Nginx) |
| **API Backend** | http://localhost:8000 | API REST FastAPI |
| **MongoDB** | localhost:27017 | Base de donnÃ©es (port interne) |
| **API Docs** | http://localhost:8000/docs | Documentation Swagger |

## ðŸ”§ Commandes utiles

### Afficher les logs
```bash
# Tous les services
docker-compose logs -f

# Service spÃ©cifique
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### ArrÃªter l'application
```bash
docker-compose down
```

### ArrÃªter et supprimer les donnÃ©es
```bash
docker-compose down -v
```

### RedÃ©marrer un service
```bash
docker-compose restart backend
```

### ExÃ©cuter une commande dans un conteneur
```bash
# AccÃ©der au shell du backend
docker-compose exec backend bash

# AccÃ©der Ã  la console MongoDB
docker-compose exec mongodb mongosh -u root -p --authenticationDatabase admin
```

### Reconstruire les images
```bash
docker-compose build --no-cache
docker-compose up -d
```

## ðŸ—ï¸ Structure des images

### Dockerfile.backend
- **Base**: Python 3.11-slim
- **Build en deux Ã©tapes** pour rÃ©duire la taille de l'image
- **Expose**: Port 8000
- **Healthcheck**: Inclus pour monitoring

### Dockerfile.frontend
- **Base**: Nginx alpine
- **Proxy**: Redirige les requÃªtes `/api/` vers le backend
- **Expose**: Port 80
- **Healthcheck**: Inclus pour monitoring

### Service MongoDB
- **Image**: mongo:7.0
- **Volume**: Persistance des donnÃ©es dans `mongodb_data`
- **Authentification**: Utilisateur root avec mot de passe

## ðŸŒ Nginx Configuration

La configuration Nginx dans `nginx.conf` :
- Sert les fichiers statiques du frontend
- Proxy les requÃªtes API vers le backend
- GÃ¨re le cache des assets
- Configure les headers CORS

## ðŸ“Š Volumes et Persistance

| Volume | Usage |
|--------|-------|
| `mongodb_data` | DonnÃ©es MongoDB persistantes |
| `mongodb_config` | Configuration MongoDB |
| `./logs` | Logs de l'application (volume local) |
| `./web` | Fichiers frontend (volume read-only) |

## ðŸ”’ SÃ©curitÃ© en Production

Avant de dÃ©ployer en production :

1. **Changez tous les mots de passe par dÃ©faut** dans le `.env`
2. **GÃ©nÃ©rez une clÃ© secrÃ¨te forte** pour JWT
3. **Configurez CORS** correctement pour votre domaine
4. **Utilisez HTTPS** avec un reverse proxy (Traefik, etc.)
5. **Limitez l'accÃ¨s MongoDB** Ã  localhost uniquement
6. **Configurez des ressources limits** dans docker-compose
7. **Activez l'audit logging** 
8. **Utilisez des secrets Docker** pour les donnÃ©es sensibles

### Exemple d'ajout de limites de ressources

```yaml
backend:
  # ... autres config ...
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 512M
      reservations:
        cpus: '0.5'
        memory: 256M
```

## ðŸ› DÃ©pannage

### Le backend ne peut pas se connecter Ã  MongoDB

```bash
# VÃ©rifier que MongoDB est running
docker-compose ps mongodb

# VÃ©rifier les logs
docker-compose logs mongodb

# VÃ©rifier la connectivitÃ©
docker-compose exec backend ping mongodb
```

### Le frontend retourne 404 pour les routes

C'est normal ! Nginx redirige toutes les requÃªtes vers `index.html` pour supporter le routing SPA.

### Les changements au frontend ne s'appliquent pas

```bash
# ArrÃªter et reconstruire le frontend
docker-compose down frontend
docker-compose build frontend
docker-compose up -d frontend
```

### ProblÃ¨mes de permissions

```bash
# RÃ©initialiser les permissions
docker-compose exec -u root backend chown -R app:app /app
```

## ðŸ“ˆ Monitoring et Logs

### VÃ©rifier les mÃ©triques
```bash
docker stats jadus-backend jadus-frontend jadus-mongodb
```

### AccÃ©der aux logs structurÃ©s
```bash
docker-compose logs backend | grep "level.*error"
```

## ðŸ”„ Mise Ã  jour

Pour mettre Ã  jour une image :

```bash
# Mettre Ã  jour le code
git pull

# Reconstruire l'image
docker-compose build <service>

# RedÃ©marrer le service
docker-compose up -d <service>
```

## ðŸ“ Notes importantes

- Les fichiers `.env` ne doivent jamais Ãªtre commitÃ©s dans Git
- Utilisez `.env.example` comme template
- Les secrets sensibles doivent Ãªtre gÃ©rÃ©s avec Docker Secrets en production
- MongoDB est accessible uniquement sur le rÃ©seau interne (`jadus-network`)
- Le frontend fait un proxy des requÃªtes API, donc pas besoin de configurer CORS sur le frontend

## ðŸ¤ Support

Pour plus d'informations :
- Documentation FastAPI: https://fastapi.tiangolo.com/
- Documentation MongoDB: https://docs.mongodb.com/
- Documentation Nginx: https://nginx.org/en/docs/

