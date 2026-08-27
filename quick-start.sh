#!/bin/bash
# Quick Start Script pour dÃ©marrer le jadus Server avec TLS en dÃ©veloppement

set -e

echo "=================================="
echo "ðŸ” jadus Server - TLS Setup"
echo "=================================="

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. VÃ©rifier que Docker est installÃ©
echo ""
echo -e "${YELLOW}[1/5]${NC} VÃ©rification de Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}âŒ Docker n'est pas installÃ©${NC}"
    exit 1
fi
echo -e "${GREEN}âœ“ Docker trouvÃ©${NC}"

# 2. VÃ©rifier que Docker Compose est installÃ©
echo ""
echo -e "${YELLOW}[2/5]${NC} VÃ©rification de Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}âŒ Docker Compose n'est pas installÃ©${NC}"
    exit 1
fi
echo -e "${GREEN}âœ“ Docker Compose trouvÃ©${NC}"

# 3. GÃ©nÃ©rer les certificats s'ils n'existent pas
echo ""
echo -e "${YELLOW}[3/5]${NC} Gestion des certificats TLS..."
if [ ! -d "./certs" ] || [ ! -f "./certs/api.pem" ]; then
    echo "GÃ©nÃ©ration des certificats auto-signÃ©s..."
    
    if [ -x "./generate-certs.sh" ]; then
        bash ./generate-certs.sh
        echo -e "${GREEN}âœ“ Certificats gÃ©nÃ©rÃ©s avec succÃ¨s${NC}"
    else
        echo -e "${RED}âŒ Script generate-certs.sh non trouvÃ©${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}âœ“ Certificats existants trouvÃ©s${NC}"
    echo "  - $(ls -lh ./certs/api.pem | awk '{print $9, $5}')"
fi

# 4. CrÃ©er le fichier .env s'il n'existe pas
echo ""
echo -e "${YELLOW}[4/5]${NC} Configuration des variables d'environnement..."
if [ ! -f "./.env" ]; then
    if [ -f "./.env.example" ]; then
        cp ./.env.example ./.env
        echo -e "${GREEN}âœ“ .env crÃ©Ã© depuis .env.example${NC}"
        echo "  âš ï¸  Assurez-vous de modifier .env avec vos paramÃ¨tres"
    fi
else
    echo -e "${GREEN}âœ“ .env existant trouvÃ©${NC}"
fi

# 5. Lancer Docker Compose
echo ""
echo -e "${YELLOW}[5/5]${NC} DÃ©marrage des services Docker..."
docker-compose down 2>/dev/null || true
docker-compose up -d --build

echo ""
echo "=================================="
echo -e "${GREEN}âœ… Services en cours de dÃ©marrage...${NC}"
echo "=================================="
echo ""
echo "ðŸ“Œ Services attendus :"
sleep 5
docker-compose ps

echo ""
echo "=================================="
echo "ðŸ”— URLs d'accÃ¨s :"
echo "=================================="
echo "  ðŸŒ Frontend    : https://localhost"
echo "  ðŸ“š API Docs    : https://localhost/api/docs"
echo "  ðŸ¥ Health      : https://localhost/health"
echo ""
echo "âš ï¸  Certificat auto-signÃ© = avertissement navigateur (normal)"
echo ""
echo "ðŸ“– Documentation complÃ¨te: ./TLS_SETUP.md"
echo ""

# Afficher les logs
echo -e "${YELLOW}Logs des services (Ctrl+C pour arrÃªter):${NC}"
docker-compose logs -f

