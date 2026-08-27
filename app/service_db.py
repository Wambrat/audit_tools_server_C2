import os
from fastapi import FastAPI
from app.logger import get_logger, setup_logging

setup_logging(
    app_name=os.getenv("JADUS_DB_SERVICE_NAME", "JadusDB"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    service_name="db",
)

logger = get_logger("app.service_db")
logger.info("JadusDB service initialized")

app = FastAPI(title="JadusDB", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "JadusDB"}
