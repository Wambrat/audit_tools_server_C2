#!/bin/bash
# Quick Start Script pour démarrer le C2 Server avec TLS en développement

set -e

echo "=================================="
echo "🔐 C2 Server - TLS Setup"
echo "=================================="

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier que Docker est installé
echo ""
echo -e "${YELLOW}[1/5]${NC} Vérification de Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker trouvé${NC}"

# 2. Vérifier que Docker Compose est installé
echo ""
echo -e "${YELLOW}[2/5]${NC} Vérification de Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose n'est pas installé${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose trouvé${NC}"

# 3. Générer les certificats s'ils n'existent pas
echo ""
echo -e "${YELLOW}[3/5]${NC} Gestion des certificats TLS..."
if [ ! -d "./certs" ] || [ ! -f "./certs/api.pem" ]; then
    echo "Génération des certificats auto-signés..."
    
    if [ -x "./generate-certs.sh" ]; then
        bash ./generate-certs.sh
        echo -e "${GREEN}✓ Certificats générés avec succès${NC}"
    else
        echo -e "${RED}❌ Script generate-certs.sh non trouvé${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Certificats existants trouvés${NC}"
    echo "  - $(ls -lh ./certs/api.pem | awk '{print $9, $5}')"
fi

# 4. Créer le fichier .env s'il n'existe pas
echo ""
echo -e "${YELLOW}[4/5]${NC} Configuration des variables d'environnement..."
if [ ! -f "./.env" ]; then
    if [ -f "./.env.example" ]; then
        cp ./.env.example ./.env
        echo -e "${GREEN}✓ .env créé depuis .env.example${NC}"
        echo "  ⚠️  Assurez-vous de modifier .env avec vos paramètres"
    fi
else
    echo -e "${GREEN}✓ .env existant trouvé${NC}"
fi

# 5. Lancer Docker Compose
echo ""
echo -e "${YELLOW}[5/5]${NC} Démarrage des services Docker..."
docker-compose down 2>/dev/null || true
docker-compose up -d --build

echo ""
echo "=================================="
echo -e "${GREEN}✅ Services en cours de démarrage...${NC}"
echo "=================================="
echo ""
echo "📌 Services attendus :"
sleep 5
docker-compose ps

echo ""
echo "=================================="
echo "🔗 URLs d'accès :"
echo "=================================="
echo "  🌐 Frontend    : https://localhost"
echo "  📚 API Docs    : https://localhost/api/docs"
echo "  🏥 Health      : https://localhost/health"
echo ""
echo "⚠️  Certificat auto-signé = avertissement navigateur (normal)"
echo ""
echo "📖 Documentation complète: ./TLS_SETUP.md"
echo ""

# Afficher les logs
echo -e "${YELLOW}Logs des services (Ctrl+C pour arrêter):${NC}"
docker-compose logs -f
