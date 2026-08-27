# Guide Docker pour l'Application Jadus Audit

Ce guide explique comment utiliser les images Docker pour déployer l'application Jadus Audit complète avec le backend, MongoDB et le frontend.

## 📋 Prérequis

- Docker (version 20.10 ou supérieure)
- Docker Compose (version 1.29 ou supérieure)
- Au minimum 2GB de RAM disponible

## 🚀 Démarrage rapide

### 1. Configuration de l'environnement

Avant de démarrer, créez un fichier `.env` à la racine du projet :

```bash
cp .env.example .env
```

Éditez le fichier `.env` et mettez à jour les valeurs sensibles :
- `MONGO_INITDB_ROOT_PASSWORD`: Changez le mot de passe MongoDB
- `SECRET_KEY`: Générez une clé secrète pour JWT
- `CORS_ORIGINS`: Ajoutez vos domaines autorisés

### 2. Lancer l'application

```bash
docker-compose up -d
```

Cela va :
- Créer et démarrer le conteneur MongoDB
- Créer et démarrer le conteneur backend FastAPI
- Créer et démarrer le conteneur frontend Nginx

### 3. Vérifier que tout fonctionne

```bash
# Vérifier l'état des conteneurs
docker-compose ps

# Consulter les logs
docker-compose logs -f

# Tester l'API backend
curl http://localhost:8000/health

# Tester le frontend
curl http://localhost/health
```

## 📍 Accès aux services

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost | Interface web (Nginx) |
| **API Backend** | http://localhost:8000 | API REST FastAPI |
| **MongoDB** | localhost:27017 | Base de données (port interne) |
| **API Docs** | http://localhost:8000/docs | Documentation Swagger |

## 🔧 Commandes utiles

### Afficher les logs
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### Arrêter l'application
```bash
docker-compose down
```

### Arrêter et supprimer les données
```bash
docker-compose down -v
```

### Redémarrer un service
```bash
docker-compose restart backend
```

### Exécuter une commande dans un conteneur
```bash
# Accéder au shell du backend
docker-compose exec backend bash

# Accéder à la console MongoDB
docker-compose exec mongodb mongosh -u root -p --authenticationDatabase admin
```

### Reconstruire les images
```bash
docker-compose build --no-cache
docker-compose up -d
```

## 🏗️ Structure des images

### Dockerfile.backend
- **Base**: Python 3.11-slim
- **Build en deux étapes** pour réduire la taille de l'image
- **Expose**: Port 8000
- **Healthcheck**: Inclus pour monitoring

### Dockerfile.frontend
- **Base**: Nginx alpine
- **Proxy**: Redirige les requêtes `/api/` vers le backend
- **Expose**: Port 80
- **Healthcheck**: Inclus pour monitoring

### Service MongoDB
- **Image**: mongo:7.0
- **Volume**: Persistance des données dans `mongodb_data`
- **Authentification**: Utilisateur root avec mot de passe

## 🌐 Nginx Configuration

La configuration Nginx dans `nginx.conf` :
- Sert les fichiers statiques du frontend
- Proxy les requêtes API vers le backend
- Gère le cache des assets
- Configure les headers CORS

## 📊 Volumes et Persistance

| Volume | Usage |
|--------|-------|
| `mongodb_data` | Données MongoDB persistantes |
| `mongodb_config` | Configuration MongoDB |
| `./logs` | Logs de l'application (volume local) |
| `./web` | Fichiers frontend (volume read-only) |

## 🔒 Sécurité en Production

Avant de déployer en production :

1. **Changez tous les mots de passe par défaut** dans le `.env`
2. **Générez une clé secrète forte** pour JWT
3. **Configurez CORS** correctement pour votre domaine
4. **Utilisez HTTPS** avec un reverse proxy (Traefik, etc.)
5. **Limitez l'accès MongoDB** à localhost uniquement
6. **Configurez des ressources limits** dans docker-compose
7. **Activez l'audit logging** 
8. **Utilisez des secrets Docker** pour les données sensibles

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

## 🐛 Dépannage

### Le backend ne peut pas se connecter à MongoDB

```bash
# Vérifier que MongoDB est running
docker-compose ps mongodb

# Vérifier les logs
docker-compose logs mongodb

# Vérifier la connectivité
docker-compose exec backend ping mongodb
```

### Le frontend retourne 404 pour les routes

C'est normal ! Nginx redirige toutes les requêtes vers `index.html` pour supporter le routing SPA.

### Les changements au frontend ne s'appliquent pas

```bash
# Arrêter et reconstruire le frontend
docker-compose down frontend
docker-compose build frontend
docker-compose up -d frontend
```

### Problèmes de permissions

```bash
# Réinitialiser les permissions
docker-compose exec -u root backend chown -R app:app /app
```

## 📈 Monitoring et Logs

### Vérifier les métriques
```bash
docker stats jadus-backend jadus-frontend jadus-mongodb
```

### Accéder aux logs structurés
```bash
docker-compose logs backend | grep "level.*error"
```

## 🔄 Mise à jour

Pour mettre à jour une image :

```bash
# Mettre à jour le code
git pull

# Reconstruire l'image
docker-compose build <service>

# Redémarrer le service
docker-compose up -d <service>
```

## 📝 Notes importantes

- Les fichiers `.env` ne doivent jamais être commités dans Git
- Utilisez `.env.example` comme template
- Les secrets sensibles doivent être gérés avec Docker Secrets en production
- MongoDB est accessible uniquement sur le réseau interne (`jadus-network`)
- Le frontend fait un proxy des requêtes API, donc pas besoin de configurer CORS sur le frontend

## 🤝 Support

Pour plus d'informations :
- Documentation FastAPI: https://fastapi.tiangolo.com/
- Documentation MongoDB: https://docs.mongodb.com/
- Documentation Nginx: https://nginx.org/en/docs/
