# ðŸ” TLS/HTTPS Configuration Guide

Ce guide explique comment configurer TLS/chiffrement complet pour dÃ©veloppement avec certificats auto-signÃ©s.

## Architecture TLS

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                 Client Browser (HTTPS)                  â”‚
â”‚                  https://localhost:443                  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                            â†“
         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
         â”‚   Traefik (Reverse Proxy)            â”‚
         â”‚   - Termine TLS/SSL                  â”‚
         â”‚   - Certificat: api.pem (auto-signÃ©) â”‚
         â”‚   - Ports: 80â†’443 redirect           â”‚
         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
          â†™                                    â†˜
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”              â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Frontend (Nginx)    â”‚              â”‚  Backend (FastAPI)   â”‚
â”‚  Port: 80 (interne)  â”‚              â”‚  Port: 8000 (interne)â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                             â†“
                                   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                                   â”‚  MongoDB (TLS)       â”‚
                                   â”‚  - Port: 27017 (TLS) â”‚
                                   â”‚  - Cert: mongodb.pem â”‚
                                   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Installation

### 1. GÃ©nÃ©rer les Certificats Auto-signÃ©s

```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1

# ou avec bash (WSL/Linux)
bash ./generate-certs.sh
```

**RÃ©sultat :**
```
certs/
â”œâ”€â”€ ca.pem                 (CA Certificate - autorite)
â”œâ”€â”€ ca-key.pem            (CA Private Key - confidentiel)
â”œâ”€â”€ mongodb-combined.pem  (MongoDB: cert + key)
â”œâ”€â”€ api.pem               (API/Nginx Certificate)
â”œâ”€â”€ api-key.pem           (API/Nginx Private Key)
â””â”€â”€ api-san.conf          (Configuration SubjectAltNames)
```

### 2. (Optionnel) Ajouter le CA au SystÃ¨me

Pour Ã©viter les avertissements "certificat non fiable" :

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

Le `.env` est dÃ©jÃ  configurÃ© avec TLS :

```env
# MongoDB avec TLS
MONGODB_URI=mongodb://root:password@mongodb:27017/...&tls=true&tlsCAFile=/etc/mongodb/ca.pem

# CORS en HTTPS
ALLOWED_ORIGINS=["https://localhost", "https://127.0.0.1"]
```

### 4. DÃ©marrer les Services

```powershell
# Build et lancer
docker-compose down
docker-compose up -d --build

# VÃ©rifier les services
docker-compose ps

# Expected output:
# jadus-traefik    Up (healthy)
# jadus-mongodb    Up (healthy)  
# jadus-backend    Up (healthy)
# jadus-frontend   Up (healthy)
```

## AccÃ¨s aux Services

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend/Panel** | `https://localhost` | HTTPS via Traefik |
| **API Swagger** | `https://localhost/api/docs` | Documentaton API |
| **API Direct** | `https://localhost/api/...` | Endpoints via Traefik |
| **Health Check** | `https://localhost/health` | Status page |

### Accepter le Certificat Auto-SignÃ©

1. Naviguer vers `https://localhost`
2. Le navigateur affiche **"Certificat non approuvÃ©"**
3. Cliquer sur **"DÃ©tails"** â†’ **"Continuer vers localhost"**
4. Le navigateur mÃ©morise la dÃ©cision

Ou importer le CA (voir section 2 ci-dessus).

## VÃ©rification du Chiffrement

### Via Browser DevTools

1. Ouvrir **DevTools** (F12)
2. Aller Ã  l'onglet **Network**
3. Chercher une requÃªte vers `/api`
4. Dans **Headers** â†’ **General**:
   ```
   Protocol: h2 (HTTP/2 sur TLS)
   ```

### Via Ligne de Commande

```powershell
# VÃ©rifier certificat TLS frontend
openssl s_client -connect localhost:443 -servername localhost

# VÃ©rifier certificat MongoDB
openssl s_client -connect localhost:27017 -showcerts
```

## DÃ©pannage

### "Certificate Verification Failed" au login

**Cause :** Certificat auto-signÃ© non fiable

**Solution :**
1. Importer le CA (voir section 2)
2. OU accepter manuellement le certificat dans le navigateur
3. OU ajouter `-k` flag Ã  curl: `curl -k https://localhost/api/login`

### MongoDB Connection Fails

**Log :** `TLSERROR handshake`

**Solutions :**
```powershell
# 1. VÃ©rifier les certificats existent
Test-Path ./certs/mongodb-combined.pem
Test-Path ./certs/ca.pem

# 2. VÃ©rifier les permissions
Get-Item ./certs/ | Get-ACL

# 3. RedÃ©marrer MongoDB
docker-compose restart mongodb

# 4. VÃ©rifier les logs
docker-compose logs mongodb -f
```

### Traefik n'expose pas HTTPS

**Cause :** Les certificats ne sont pas montÃ©s correctement

**VÃ©rifier :**
```powershell
# Logs Traefik
docker-compose logs traefik

# Certificats dans le volume
docker exec jadus-traefik ls -la /etc/traefik/certs/
```

## Configuration AvancÃ©e

### Renouveler les Certificats

Les certificats durent **365 jours**. Pour en gÃ©nÃ©rer de nouveaux :

```powershell
# Supprimer les anciens
Remove-Item ./certs -Recurse -Force

# RegÃ©nÃ©rer
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1

# RedÃ©marrer services
docker-compose restart traefik mongodb backend
```

### Certificats Production (Let's Encrypt)

Pour production avec domaine rÃ©el :

```powershell
# Utiliser Traefik avec Let's Encrypt automatiquement
# Configuration supplÃ©mentaire requise dans docker-compose.yml
```

### Augmenter la ValiditÃ© des Certificats

Dans `generate-certs.ps1`, modifier :
```powershell
$Days = 365  # â† Changer Ã  1825 (5 ans)
```

## SecuritÃ©

### âš ï¸ DÃ©veloppement SEULEMENT

Les certificats auto-signÃ©s ne doivent Ãªtre utilisÃ©s que pour :
- âœ… DÃ©veloppement local
- âœ… Tests internes
- âœ… Environnement de staging

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

## RÃ©fÃ©rences

- [Traefik Documentation](https://doc.traefik.io/)
- [MongoDB TLS](https://docs.mongodb.com/manual/tutorial/configure-ssl/)
- [OpenSSL Certificates](https://www.openssl.org/)
- [HTTPS Standards](https://tools.ietf.org/html/rfc8446)

## Commandes Utiles

```powershell
# Afficher le certificat
openssl x509 -in ./certs/api.pem -text -noout

# VÃ©rifier la chaÃ®ne certificats
openssl verify -CAfile ./certs/ca.pem ./certs/api.pem

# Test de connexion HTTPS
curl -k https://localhost/health

# Tester l'API avec certificat
curl -k --cert ./certs/api.pem --key ./certs/api-key.pem https://localhost/api/admin/login
```

