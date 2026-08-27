# jadus

Plateforme d’audit et de supervision de parc informatique, avec une API FastAPI, un tableau de bord web et une base MongoDB.

## Vue d’ensemble

jadus permet de :
- enregistrer des agents PowerShell
- distribuer des tâches d’audit
- récupérer des résultats sécurisés
- consulter l’état des systèmes depuis un portail web

## Architecture

- API: Python + FastAPI
- Frontend: Vue.js servi par un worker web dédié
- Base: MongoDB
- Proxy: Traefik avec HTTPS sur localhost

## Démarrage rapide

### Avec Docker

```bash
docker compose -p jadus up -d --build
```

Services exposés :
- https://localhost/
- https://localhost/api/
- http://localhost:8001/health
- http://localhost:8003/health

### Sans Docker

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Points d’entrée

- API backend: http://localhost:8001
- Frontend web: https://localhost/
- Documentation OpenAPI: https://localhost/api/docs

## Structure principale

- app/: logique backend et routes API
- web/: interface web statique
- logs/: journaux par service
- certs/: certificats TLS
- docker-compose.yml: orchestration des services

## Sécurité et observabilité

- JWT admin
- rate limiting
- logs séparés par service
- headers HTTP renforcés
- TLS via Traefik
