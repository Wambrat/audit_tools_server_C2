# 🔐 TLS/HTTPS Configuration Guide

Ce guide explique comment configurer TLS/chiffrement complet pour développement avec certificats auto-signés.

## Architecture TLS

```
┌─────────────────────────────────────────────────────────┐
│                 Client Browser (HTTPS)                  │
│                  https://localhost:443                  │
└─────────────────────────────────────────────────────────┘
                            ↓
         ┌──────────────────────────────────────┐
         │   Traefik (Reverse Proxy)            │
         │   - Termine TLS/SSL                  │
         │   - Certificat: api.pem (auto-signé) │
         │   - Ports: 80→443 redirect           │
         └──────────────────────────────────────┘
          ↙                                    ↘
┌──────────────────────┐              ┌──────────────────────┐
│  Frontend (Nginx)    │              │  Backend (FastAPI)   │
│  Port: 80 (interne)  │              │  Port: 8000 (interne)│
└──────────────────────┘              └──────────────────────┘
                                             ↓
                                   ┌──────────────────────┐
                                   │  MongoDB (TLS)       │
                                   │  - Port: 27017 (TLS) │
                                   │  - Cert: mongodb.pem │
                                   └──────────────────────┘
```

## Installation

### 1. Générer les Certificats Auto-signés

```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1

# ou avec bash (WSL/Linux)
bash ./generate-certs.sh
```

**Résultat :**
```
certs/
├── ca.pem                 (CA Certificate - autorite)
├── ca-key.pem            (CA Private Key - confidentiel)
├── mongodb-combined.pem  (MongoDB: cert + key)
├── api.pem               (API/Nginx Certificate)
├── api-key.pem           (API/Nginx Private Key)
└── api-san.conf          (Configuration SubjectAltNames)
```

### 2. (Optionnel) Ajouter le CA au Système

Pour éviter les avertissements "certificat non fiable" :

**Windows (Admin):**
```powershell
certutil -addstore -f 'Root' .\certs\ca.pem
```

**macOS:**
```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ./certs/ca.pem
```

**Linux:**
```bash
sudo cp ./certs/ca.pem /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

### 3. Configuration Environment Variables

Le `.env` est déjà configuré avec TLS :

```env
# MongoDB avec TLS
MONGODB_URI=mongodb://root:password@mongodb:27017/...&tls=true&tlsCAFile=/etc/mongodb/ca.pem

# CORS en HTTPS
ALLOWED_ORIGINS=["https://localhost", "https://127.0.0.1"]
```

### 4. Démarrer les Services

```powershell
# Build et lancer
docker-compose down
docker-compose up -d --build

# Vérifier les services
docker-compose ps

# Expected output:
# c2-traefik    Up (healthy)
# c2-mongodb    Up (healthy)  
# c2-backend    Up (healthy)
# c2-frontend   Up (healthy)
```

## Accès aux Services

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend/Panel** | `https://localhost` | HTTPS via Traefik |
| **API Swagger** | `https://localhost/api/docs` | Documentaton API |
| **API Direct** | `https://localhost/api/...` | Endpoints via Traefik |
| **Health Check** | `https://localhost/health` | Status page |

### Accepter le Certificat Auto-Signé

1. Naviguer vers `https://localhost`
2. Le navigateur affiche **"Certificat non approuvé"**
3. Cliquer sur **"Détails"** → **"Continuer vers localhost"**
4. Le navigateur mémorise la décision

Ou importer le CA (voir section 2 ci-dessus).

## Vérification du Chiffrement

### Via Browser DevTools

1. Ouvrir **DevTools** (F12)
2. Aller à l'onglet **Network**
3. Chercher une requête vers `/api`
4. Dans **Headers** → **General**:
   ```
   Protocol: h2 (HTTP/2 sur TLS)
   ```

### Via Ligne de Commande

```powershell
# Vérifier certificat TLS frontend
openssl s_client -connect localhost:443 -servername localhost

# Vérifier certificat MongoDB
openssl s_client -connect localhost:27017 -showcerts
```

## Dépannage

### "Certificate Verification Failed" au login

**Cause :** Certificat auto-signé non fiable

**Solution :**
1. Importer le CA (voir section 2)
2. OU accepter manuellement le certificat dans le navigateur
3. OU ajouter `-k` flag à curl: `curl -k https://localhost/api/login`

### MongoDB Connection Fails

**Log :** `TLSERROR handshake`

**Solutions :**
```powershell
# 1. Vérifier les certificats existent
Test-Path ./certs/mongodb-combined.pem
Test-Path ./certs/ca.pem

# 2. Vérifier les permissions
Get-Item ./certs/ | Get-ACL

# 3. Redémarrer MongoDB
docker-compose restart mongodb

# 4. Vérifier les logs
docker-compose logs mongodb -f
```

### Traefik n'expose pas HTTPS

**Cause :** Les certificats ne sont pas montés correctement

**Vérifier :**
```powershell
# Logs Traefik
docker-compose logs traefik

# Certificats dans le volume
docker exec c2-traefik ls -la /etc/traefik/certs/
```

## Configuration Avancée

### Renouveler les Certificats

Les certificats durent **365 jours**. Pour en générer de nouveaux :

```powershell
# Supprimer les anciens
Remove-Item ./certs -Recurse -Force

# Regénérer
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1

# Redémarrer services
docker-compose restart traefik mongodb backend
```

### Certificats Production (Let's Encrypt)

Pour production avec domaine réel :

```powershell
# Utiliser Traefik avec Let's Encrypt automatiquement
# Configuration supplémentaire requise dans docker-compose.yml
```

### Augmenter la Validité des Certificats

Dans `generate-certs.ps1`, modifier :
```powershell
$Days = 365  # ← Changer à 1825 (5 ans)
```

## Securité

### ⚠️ Développement SEULEMENT

Les certificats auto-signés ne doivent être utilisés que pour :
- ✅ Développement local
- ✅ Tests internes
- ✅ Environnement de staging

Ne PAS utiliser en production publique !

### Production : Let's Encrypt

```toml
# Traefik configuration (snippet)
[certificatesResolvers.letsencrypt.acme]
  email = "admin@example.com"
  storage = "/traefik/acme.json"
  [certificatesResolvers.letsencrypt.acme.httpChallenge]
    entryPoint = "web"
```

## Références

- [Traefik Documentation](https://doc.traefik.io/)
- [MongoDB TLS](https://docs.mongodb.com/manual/tutorial/configure-ssl/)
- [OpenSSL Certificates](https://www.openssl.org/)
- [HTTPS Standards](https://tools.ietf.org/html/rfc8446)

## Commandes Utiles

```powershell
# Afficher le certificat
openssl x509 -in ./certs/api.pem -text -noout

# Vérifier la chaîne certificats
openssl verify -CAfile ./certs/ca.pem ./certs/api.pem

# Test de connexion HTTPS
curl -k https://localhost/health

# Tester l'API avec certificat
curl -k --cert ./certs/api.pem --key ./certs/api-key.pem https://localhost/api/admin/login
```
