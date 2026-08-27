# 🔐 TLS/HTTPS Configuration - Démarrage Rapide

## Qu'est-ce qui a changé?

Votre Jadus Audit utilise maintenant **HTTPS/TLS** pour le chiffrement complet:

| Avant | Maintenant |
|-------|-----------|
| HTTP (non chiffré) | **HTTPS (chiffré)** ✅ |
| Pas de reverse proxy | **Traefik (reverse proxy)** ✅ |
| MongoDB en HTTP | **MongoDB TLS** ✅ |
| CORS HTTP | **CORS HTTPS** ✅ |

## 🚀 Démarrer le Serveur TLS

### Option 1: Automatique (Recommandé)

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
# 1. Générer les certificats (une seule fois)
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1

# 2. Démarrer les services
docker-compose up -d --build

# 3. Accéder à https://localhost
```

## 🌐 URLs d'Accès

```
🌐 Frontend/Panel      : https://localhost
📚 API Swagger Docs    : https://localhost/api/docs
🏥 Health Check        : https://localhost/health
```

## ⚠️ Certificat Auto-Signé

Lors du premier accès, le navigateur affiche un avertissement:

**C'est normal!** C'est parce qu'on utilise des certificats auto-signés pour le développement.

- Cliquer sur **"Continuer"** ou **"Accepter le risque"**
- Le navigateur mémorise la décision

## 🔍 Vérifier que TLS Fonctionne

```powershell
# Test simple
curl -k https://localhost/health

# Afficher le certificat
openssl s_client -connect localhost:443 -servername localhost

# Dans le navigateur (DevTools > Network):
# Voir "Protocol: h2" ou "https" = ✅ Chiffrement actif
```

## 📁 Fichiers Créés

```
certs/
├── ca.pem                    # Certificat CA (autorité)
├── mongodb-combined.pem      # MongoDB certificat+clé
├── api.pem                   # API certificat
└── api-key.pem              # API clé privée

Nouveaux fichiers:
├── generate-certs.ps1        # Script génération (Windows)
├── generate-certs.sh         # Script génération (Unix)
├── quick-start.ps1           # Démarrage automatique
├── quick-start.sh            # Démarrage automatique (Unix)
├── TLS_SETUP.md              # Documentation complète
└── traefik.toml              # Configuration Traefik
```

## 🔄 Modifications Apportées

### docker-compose.yml
- ✅ Ajout de Traefik (reverse proxy HTTPS)
- ✅ MongoDB avec TLS activé
- ✅ Backend configuration pour TLS
- ✅ Ports 443 (HTTPS) exposés

### .env & .env.example
- ✅ MONGODB_URI avec TLS (`&tls=true`)
- ✅ ALLOWED_ORIGINS en HTTPS
- ✅ TLS_ENABLED=true

### app/database_mongodb.py
- ✅ Support des certificats TLS
- ✅ Connexion sécurisée MongoDB

### main.py
- ✅ CORS configuré pour HTTPS
- ✅ Origins HTTPS/localhost ajoutés

## 🛠️ Configuration Personnalisée

### Changer le mot de passe MongoDB
Éditer `.env`:
```env
MONGO_INITDB_ROOT_PASSWORD=your_new_password
MONGODB_URI=mongodb://root:your_new_password@mongodb:27017/...
```

Redémarrer:
```powershell
docker-compose restart mongodb backend
```

### Augmenter la durée des certificats
Dans `generate-certs.ps1`:
```powershell
$Days = 1825  # 5 ans au lieu de 365 jours
```

Puis regénérer:
```powershell
Remove-Item ./certs -Recurse -Force
powershell -ExecutionPolicy Bypass -File .\generate-certs.ps1
docker-compose restart
```

## 📊 Architecture

```
Client Browser (HTTPS:443)
         ↓
    Traefik (Port 443)
         ↓
    ├─→ Frontend (Nginx)
    └─→ Backend (FastAPI)
         ↓
      MongoDB (TLS:27017)
```

## ✅ Checklist Sécurité

- ✅ Chiffrement TLS/HTTPS
- ✅ MongoDB chiffré
- ✅ JWT authentication
- ✅ CORS restrictif
- ✅ Rate limiting
- ✅ Headers de sécurité (HSTS, CSP, etc.)
- ✅ Audit logging

## ❓ FAQ

### Q: Pourquoi le certificat est auto-signé?
R: Pour le développement local. Facile à générer, libre, sûr sur réseau isolé.

### Q: Puis-je utiliser HTTP?
R: Non, le serveur n'expose que HTTPS maintenant. TLS partout! 🔒

### Q: Comment utiliser Let's Encrypt en production?
R: Voir TLS_SETUP.md section "Production".

### Q: Le certificat dure combien de temps?
R: 365 jours par défaut. Regénérer avant l'expiration.

### Q: Puis-je ignorer le warning du certificat?
R: Oui, c'est normal en développement. Importer le CA pour l'éviter.

## 📖 Docs Complètes

- **[INSTALLATION.md](./INSTALLATION.md)** - Guide d'installation complet
- **[TLS_SETUP.md](./TLS_SETUP.md)** - Documentation TLS avancée
- **[README.md](./README.md)** - Vue d'ensemble

## 🎯 Prochaines Étapes

1. Exécuter: `powershell -ExecutionPolicy Bypass -File .\quick-start.ps1`
2. Attendre que les services démarrent
3. Accéder à: `https://localhost`
4. Se connecter (admin/password défini dans .env)
5. Lire [TLS_SETUP.md](./TLS_SETUP.md) pour plus de détails

---

**Développement sécurisé = Développement productif!** 🚀🔒
