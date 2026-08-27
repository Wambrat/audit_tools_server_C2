# ðŸ” TLS/HTTPS Configuration - DÃ©marrage Rapide

## Qu'est-ce qui a changÃ©?

Votre Jadus Audit utilise maintenant **HTTPS/TLS** pour le chiffrement complet:

| Avant | Maintenant |
|-------|-----------|
| HTTP (non chiffrÃ©) | **HTTPS (chiffrÃ©)** âœ… |
| Pas de reverse proxy | **Traefik (reverse proxy)** âœ… |
| MongoDB en HTTP | **MongoDB TLS** âœ… |
| CORS HTTP | **CORS HTTPS** âœ… |

## ðŸš€ DÃ©marrer le Serveur TLS

### Option 1: Automatique (RecommandÃ©)

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File .\quick-start.ps1
```

**Linux/macOS:**
```bash
bash ./quick-start.sh
```

### Option 2: Manuel

```powershell
# 1. GÃ©nÃ©rer les certificats (une seule fois)
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1

# 2. DÃ©marrer les services
docker-compose up -d --build

# 3. AccÃ©der Ã  https://localhost
```

## ðŸŒ URLs d'AccÃ¨s

```
ðŸŒ Frontend/Panel      : https://localhost
ðŸ“š API Swagger Docs    : https://localhost/api/docs
ðŸ¥ Health Check        : https://localhost/health
```

## âš ï¸ Certificat Auto-SignÃ©

Lors du premier accÃ¨s, le navigateur affiche un avertissement:

**C'est normal!** C'est parce qu'on utilise des certificats auto-signÃ©s pour le dÃ©veloppement.

- Cliquer sur **"Continuer"** ou **"Accepter le risque"**
- Le navigateur mÃ©morise la dÃ©cision

## ðŸ” VÃ©rifier que TLS Fonctionne

```powershell
# Test simple
curl -k https://localhost/health

# Afficher le certificat
openssl s_client -connect localhost:443 -servername localhost

# Dans le navigateur (DevTools > Network):
# Voir "Protocol: h2" ou "https" = âœ… Chiffrement actif
```

## ðŸ“ Fichiers CrÃ©Ã©s

```
certs/
â”œâ”€â”€ ca.pem                    # Certificat CA (autoritÃ©)
â”œâ”€â”€ mongodb-combined.pem      # MongoDB certificat+clÃ©
â”œâ”€â”€ api.pem                   # API certificat
â””â”€â”€ api-key.pem              # API clÃ© privÃ©e

Nouveaux fichiers:
â”œâ”€â”€ generate-certs.ps1        # Script gÃ©nÃ©ration (Windows)
â”œâ”€â”€ generate-certs.sh         # Script gÃ©nÃ©ration (Unix)
â”œâ”€â”€ quick-start.ps1           # DÃ©marrage automatique
â”œâ”€â”€ quick-start.sh            # DÃ©marrage automatique (Unix)
â”œâ”€â”€ TLS_SETUP.md              # Documentation complÃ¨te
â””â”€â”€ traefik.toml              # Configuration Traefik
```

## ðŸ”„ Modifications ApportÃ©es

### docker-compose.yml
- âœ… Ajout de Traefik (reverse proxy HTTPS)
- âœ… MongoDB avec TLS activÃ©
- âœ… Backend configuration pour TLS
- âœ… Ports 443 (HTTPS) exposÃ©s

### .env & .env.example
- âœ… MONGODB_URI avec TLS (`&tls=true`)
- âœ… ALLOWED_ORIGINS en HTTPS
- âœ… TLS_ENABLED=true

### app/database_mongodb.py
- âœ… Support des certificats TLS
- âœ… Connexion sÃ©curisÃ©e MongoDB

### main.py
- âœ… CORS configurÃ© pour HTTPS
- âœ… Origins HTTPS/localhost ajoutÃ©s

## ðŸ› ï¸ Configuration PersonnalisÃ©e

### Changer le mot de passe MongoDB
Ã‰diter `.env`:
```env
MONGO_INITDB_ROOT_PASSWORD=your_new_password
MONGODB_URI=mongodb://root:your_new_password@mongodb:27017/...
```

RedÃ©marrer:
```powershell
docker-compose restart mongodb backend
```

### Augmenter la durÃ©e des certificats
Dans `generate-certs.ps1`:
```powershell
$Days = 1825  # 5 ans au lieu de 365 jours
```

Puis regÃ©nÃ©rer:
```powershell
Remove-Item ./certs -Recurse -Force
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1
docker-compose restart
```

## ðŸ“Š Architecture

```
Client Browser (HTTPS:443)
         â†“
    Traefik (Port 443)
         â†“
    â”œâ”€â†’ Frontend (Nginx)
    â””â”€â†’ Backend (FastAPI)
         â†“
      MongoDB (TLS:27017)
```

## âœ… Checklist SÃ©curitÃ©

- âœ… Chiffrement TLS/HTTPS
- âœ… MongoDB chiffrÃ©
- âœ… JWT authentication
- âœ… CORS restrictif
- âœ… Rate limiting
- âœ… Headers de sÃ©curitÃ© (HSTS, CSP, etc.)
- âœ… Audit logging

## â“ FAQ

### Q: Pourquoi le certificat est auto-signÃ©?
R: Pour le dÃ©veloppement local. Facile Ã  gÃ©nÃ©rer, libre, sÃ»r sur rÃ©seau isolÃ©.

### Q: Puis-je utiliser HTTP?
R: Non, le serveur n'expose que HTTPS maintenant. TLS partout! ðŸ”’

### Q: Comment utiliser Let's Encrypt en production?
R: Voir TLS_SETUP.md section "Production".

### Q: Le certificat dure combien de temps?
R: 365 jours par dÃ©faut. RegÃ©nÃ©rer avant l'expiration.

### Q: Puis-je ignorer le warning du certificat?
R: Oui, c'est normal en dÃ©veloppement. Importer le CA pour l'Ã©viter.

## ðŸ“– Docs ComplÃ¨tes

- **[INSTALLATION.md](./INSTALLATION.md)** - Guide d'installation complet
- **[TLS_SETUP.md](./TLS_SETUP.md)** - Documentation TLS avancÃ©e
- **[README.md](./README.md)** - Vue d'ensemble

## ðŸŽ¯ Prochaines Ã‰tapes

1. ExÃ©cuter: `powershell -ExecutionPolicy Bypass -File .\quick-start.ps1`
2. Attendre que les services dÃ©marrent
3. AccÃ©der Ã : `https://localhost`
4. Se connecter (admin/password dÃ©fini dans .env)
5. Lire [TLS_SETUP.md](./TLS_SETUP.md) pour plus de dÃ©tails

---

**DÃ©veloppement sÃ©curisÃ© = DÃ©veloppement productif!** ðŸš€ðŸ”’

