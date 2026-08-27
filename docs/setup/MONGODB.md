# ðŸ’¾ Configuration MongoDB - Base de DonnÃ©es pour Production

## ðŸš€ DÃ©marrage Rapide

### 1. Lancer MongoDB

**Docker (RecommandÃ©):**
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
MONGODB_DB=jadus_server
MONGODB_TIMEOUT=5000
```

### 3. Installer dÃ©pendances

```bash
pip install -r requirements.txt
# Ajoute: pymongo==4.6.0
```

### 4. DÃ©marrer l'API

```bash
python main.py
```

**RÃ©sultat attendu:**
```
ðŸŸ¢ Database mode: MongoDB (persistent)
âœ… MongoDB connected successfully
```

---

## ðŸ“Š Pourquoi MongoDB pour EDR?

| Avantage | Description |
|----------|-------------|
| **SchÃ©ma Flexible** | Chaque rÃ©sultat d'audit a sa structure propre |
| **JSON Natif** | PowerShell retourne du JSON, MongoDB le stocke directement |
| **ScalabilitÃ©** | Facile d'ajouter des centaines d'agents |
| **Performant** | Index automatiques, requÃªtes optimisÃ©es |
| **Persistance** | Les donnÃ©es restent aprÃ¨s redÃ©marrage |

---

## âš™ï¸ Configuration AvancÃ©e

### Atlas Cloud (MongoDB)

```env
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/jadus_server
```

### Authentication Locale

```env
MONGODB_URL=mongodb://user:password@localhost:27017/jadus_server?authSource=admin
```

### Replica Set (Haute DisponibilitÃ©)

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
use jadus_server

# Index par agent
db.agents.createIndex({ "agent_id": 1 })

# Index par timestamp
db.results.createIndex({ "created_at": -1 })

# Index composÃ©
db.results.createIndex({ "agent_id": 1, "created_at": -1 })
```

---

## ðŸ—„ï¸ Structure des Collections

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

## ðŸ§ª Tests MongoDB

### Tester les Connexions

```bash
python test_mongodb.py
```

**RÃ©sultat:**
```
âœ… Database connection OK
âœ… Create agent OK
âœ… List agents OK
...
âœ… ALL TESTS PASSED!
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

# VÃ©rifier
curl http://localhost:8000/api/monitoring/overview
```

---

## ðŸ”„ Migration: MÃ©moire â†’ MongoDB

Si vous avez des donnÃ©es en mÃ©moire:

```bash
python migrate_to_mongodb.py
```

**Processus:**
1. ArrÃªter l'API
2. Sauvegarder les donnÃ©es
3. Configurer DATABASE_MODE=mongodb
4. Relancer l'API
5. Tester avec `python test_mongodb.py`

---

## ðŸ“¡ RequÃªtes MongoDB

### CLI (mongosh)

```bash
mongosh
use jadus_server

# Compter les agents
db.agents.countDocuments()

# Voir tous les agents
db.agents.find()

# Agents actifs
db.agents.find({ "status": "active" })

# RÃ©sultats des 24 derniÃ¨res heures
db.results.find({ 
  "submitted_at": { 
    "$gte": new Date(Date.now() - 24*60*60*1000)
  }
})

# Taux de succÃ¨s par agent
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

# CrÃ©er agent
db.create_agent(...)

# Recherche personnalisÃ©e
results = db.results.find({"status": "success"})
for r in results:
    print(r)
```

---

## ðŸ› Troubleshooting

### Erreur: "Connection refused"

```bash
# VÃ©rifier MongoDB
docker ps | grep mongodb

# RedÃ©marrer
docker restart mongodb

# VÃ©rifier la connectivitÃ©
telnet localhost 27017
```

### Erreur: "Authentication failed"

```bash
# VÃ©rifier les credentials dans .env
cat .env | grep MONGODB

# RÃ©initialiser (Docker)
docker rm mongodb
docker run -d --name mongodb -p 27017:27017 mongo:latest
```

### Performance lente

```bash
# VÃ©rifier les index
mongosh
use jadus_server
db.agents.getIndexes()

# CrÃ©er des index manquants
db.agents.createIndex({ "agent_id": 1 })
db.results.createIndex({ "agent_id": 1, "submitted_at": -1 })
```

### DonnÃ©es perdues

- Mode mÃ©moire: Les donnÃ©es sont perdues au redÃ©marrage
- Mode MongoDB: **Les donnÃ©es persistent** sur le disque

Pour persister les donnÃ©es: `DATABASE_MODE=mongodb`

---

## ðŸ“Š Backup & Restore

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

## âš¡ Performance - Production

### Recommandations

1. **Index essentiels:**
   ```bash
   db.agents.createIndex({ "agent_id": 1 }, { unique: true })
   db.results.createIndex({ "agent_id": 1, "submitted_at": -1 })
   ```

2. **RÃ©plication (HA):**
   - Utiliser Replica Set pour la haute disponibilitÃ©
   - Minimum 3 nÅ“uds pour production

3. **Monitoring:**
   ```bash
   mongosh
   db.serverStatus()
   ```

4. **Archivage:**
   - Archiver les vieilles donnÃ©es aprÃ¨s 6 mois
   - Garder les indexes sur les donnÃ©es actives

---

## ðŸ“š Documentation

- [Architecture](../architecture/ARCHITECTURE.md)
- [Quick Start](./QUICK_START.md)
- [API Documentation](../api/API.md)
- [Testing Guide](../testing/TESTING.md)

---

## âœ… Checklist

- [ ] MongoDB lancÃ©
- [ ] MONGODB_URL configurÃ© dans .env
- [ ] `python test_mongodb.py` âœ…
- [ ] API lancÃ©e (`python main.py`)
- [ ] Agents enregistrÃ©s et actifs
- [ ] Backups configurÃ©s


