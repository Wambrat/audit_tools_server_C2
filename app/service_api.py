import os
from fastapi import FastAPI
from app.logger import get_logger, setup_logging
from app.routes import router

setup_logging(
    app_name=os.getenv("JADUS_API_SERVICE_NAME", "JadusAPI"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    service_name="api",
)

logger = get_logger("app.service_api")
logger.info("JadusAPI service initialized")

app = FastAPI(title="JadusAPI", version="1.0.0")
app.include_router(router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "JadusAPI", "route": "/"}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "JadusAPI"}
