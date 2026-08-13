# 💾 Configuration MongoDB - Base de Données pour Production

## 🚀 Démarrage Rapide

### 1. Lancer MongoDB

**Docker (Recommandé):**
```bash
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

**Local:**
```bash
# Windows: Installer puis Start-Service MongoDB
# macOS: brew install mongodb-community && brew services start mongodb-community
# Linux: apt install mongodb && systemctl start mongod
```

### 2. Configurer .env

```env
DATABASE_MODE=mongodb
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=c2_server
MONGODB_TIMEOUT=5000
```

### 3. Installer dépendances

```bash
pip install -r requirements.txt
# Ajoute: pymongo==4.6.0
```

### 4. Démarrer l'API

```bash
python main.py
```

**Résultat attendu:**
```
🟢 Database mode: MongoDB (persistent)
✅ MongoDB connected successfully
```

---

## 📊 Pourquoi MongoDB pour EDR?

| Avantage | Description |
|----------|-------------|
| **Schéma Flexible** | Chaque résultat d'audit a sa structure propre |
| **JSON Natif** | PowerShell retourne du JSON, MongoDB le stocke directement |
| **Scalabilité** | Facile d'ajouter des centaines d'agents |
| **Performant** | Index automatiques, requêtes optimisées |
| **Persistance** | Les données restent après redémarrage |

---

## ⚙️ Configuration Avancée

### Atlas Cloud (MongoDB)

```env
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/c2_server
```

### Authentication Locale

```env
MONGODB_URL=mongodb://user:password@localhost:27017/c2_server?authSource=admin
```

### Replica Set (Haute Disponibilité)

```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  mongo:latest --replSet rs0

# Initialiser
docker exec mongodb mongosh --eval "rs.initiate()"
```

### Indexation pour Performance

```bash
mongosh
use c2_server

# Index par agent
db.agents.createIndex({ "agent_id": 1 })

# Index par timestamp
db.results.createIndex({ "created_at": -1 })

# Index composé
db.results.createIndex({ "agent_id": 1, "created_at": -1 })
```

---

## 🗄️ Structure des Collections

### agents
```json
{
  "_id": ObjectId(),
  "agent_id": "uuid",
  "agent_name": "DC-AUDIT-01",
  "hostname": "DC-01",
  "username": "DOMAIN\\SYSTEM",
  "os_version": "Windows Server 2022",
  "api_key": "hashed",
  "status": "active",
  "last_beacon": "2026-06-16T17:45:14Z",
  "created_at": "2026-06-15T10:00:00Z"
}
```

### tasks
```json
{
  "_id": ObjectId(),
  "task_id": "uuid",
  "command": "Get-Process",
  "agent_id": "uuid",
  "status": "pending",
  "assigned_at": "2026-06-16T17:45:14Z",
  "completed_at": null
}
```

### results
```json
{
  "_id": ObjectId(),
  "result_id": "uuid",
  "agent_id": "uuid",
  "task_id": "uuid",
  "output": { ... },
  "status": "success",
  "submitted_at": "2026-06-16T17:46:00Z"
}
```

---

## 🧪 Tests MongoDB

### Tester les Connexions

```bash
python test_mongodb.py
```

**Résultat:**
```
✅ Database connection OK
✅ Create agent OK
✅ List agents OK
...
✅ ALL TESTS PASSED!
```

### Tester via API

```bash
# Enroll un agent
curl -X POST http://localhost:8000/api/enroll \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "TEST",
    "os_version": "Windows 10",
    "hostname": "TEST-PC",
    "username": "admin"
  }'

# Vérifier
curl http://localhost:8000/api/monitoring/overview
```

---

## 🔄 Migration: Mémoire → MongoDB

Si vous avez des données en mémoire:

```bash
python migrate_to_mongodb.py
```

**Processus:**
1. Arrêter l'API
2. Sauvegarder les données
3. Configurer DATABASE_MODE=mongodb
4. Relancer l'API
5. Tester avec `python test_mongodb.py`

---

## 📡 Requêtes MongoDB

### CLI (mongosh)

```bash
mongosh
use c2_server

# Compter les agents
db.agents.countDocuments()

# Voir tous les agents
db.agents.find()

# Agents actifs
db.agents.find({ "status": "active" })

# Résultats des 24 dernières heures
db.results.find({ 
  "submitted_at": { 
    "$gte": new Date(Date.now() - 24*60*60*1000)
  }
})

# Taux de succès par agent
db.results.aggregate([
  { "$group": {
    "_id": "$agent_id",
    "total": { "$sum": 1 },
    "success": { "$sum": { "$cond": [{ "$eq": ["$status", "success"] }, 1, 0] }}
  }}
])
```

### Python

```python
from app.database_mongodb import MongoDatabase

db = MongoDatabase()

# Lister agents
agents = db.list_agents()

# Créer agent
db.create_agent(...)

# Recherche personnalisée
results = db.results.find({"status": "success"})
for r in results:
    print(r)
```

---

## 🐛 Troubleshooting

### Erreur: "Connection refused"

```bash
# Vérifier MongoDB
docker ps | grep mongodb

# Redémarrer
docker restart mongodb

# Vérifier la connectivité
telnet localhost 27017
```

### Erreur: "Authentication failed"

```bash
# Vérifier les credentials dans .env
cat .env | grep MONGODB

# Réinitialiser (Docker)
docker rm mongodb
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

### Performance lente

```bash
# Vérifier les index
mongosh
use c2_server
db.agents.getIndexes()

# Créer des index manquants
db.agents.createIndex({ "agent_id": 1 })
db.results.createIndex({ "agent_id": 1, "submitted_at": -1 })
```

### Données perdues

- Mode mémoire: Les données sont perdues au redémarrage
- Mode MongoDB: **Les données persistent** sur le disque

Pour persister les données: `DATABASE_MODE=mongodb`

---

## 📊 Backup & Restore

### Backup complet

```bash
# Docker
docker exec mongodb mongodump --out /backup

# Local
mongodump --out /backup
```

### Restore

```bash
# Docker
docker exec mongodb mongorestore /backup

# Local
mongorestore /backup
```

---

## ⚡ Performance - Production

### Recommandations

1. **Index essentiels:**
   ```bash
   db.agents.createIndex({ "agent_id": 1 }, { unique: true })
   db.results.createIndex({ "agent_id": 1, "submitted_at": -1 })
   ```

2. **Réplication (HA):**
   - Utiliser Replica Set pour la haute disponibilité
   - Minimum 3 nœuds pour production

3. **Monitoring:**
   ```bash
   mongosh
   db.serverStatus()
   ```

4. **Archivage:**
   - Archiver les vieilles données après 6 mois
   - Garder les indexes sur les données actives

---

## 📚 Documentation

- [Architecture](../architecture/ARCHITECTURE.md)
- [Quick Start](./QUICK_START.md)
- [API Documentation](../api/API.md)
- [Testing Guide](../testing/TESTING.md)

---

## ✅ Checklist

- [ ] MongoDB lancé
- [ ] MONGODB_URL configuré dans .env
- [ ] `python test_mongodb.py` ✅
- [ ] API lancée (`python main.py`)
- [ ] Agents enregistrés et actifs
- [ ] Backups configurés

