#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p logs/api logs/web

export JADUS_SERVICE_NAME="JadusAPI"
export JADUS_API_SERVICE_NAME="JadusAPI"
export JADUS_WEB_SERVICE_NAME="JadusPanelWeb"

# Worker 1 : API
python3 -m uvicorn app.service_api:app --host 0.0.0.0 --port 8001 > logs/api/info.log 2> logs/api/error.log &
API_PID=$!

# Worker 2 : web panel
JADUS_SERVICE_NAME="JadusPanelWeb" JADUS_WEB_SERVICE_NAME="JadusPanelWeb" \
  python3 -m uvicorn app.service_web:app --host 0.0.0.0 --port 8003 > logs/web/info.log 2> logs/web/error.log &
WEB_PID=$!

echo "Jadus API worker started with PID $API_PID"
echo "Jadus PanelWeb worker started with PID $WEB_PID"

wait "$API_PID" "$WEB_PID"
