import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.logger import get_logger, setup_logging

setup_logging(
    app_name=os.getenv("JADUS_WEB_SERVICE_NAME", "JadusPanelWeb"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    service_name="web",
)

logger = get_logger("app.service_web")
logger.info("JadusPanelWeb service initialized")

app = FastAPI(title="JadusPanelWeb", version="1.0.0")
web_root = Path(__file__).resolve().parent.parent / "web"


@app.get("/")
async def root():
    return FileResponse(web_root / "index.html")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "JadusPanelWeb"}


@app.get("/{page_name}.html")
async def static_page(page_name: str):
    candidate = web_root / f"{page_name}.html"
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    return FileResponse(candidate)


app.mount("/css", StaticFiles(directory=str(web_root / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(web_root / "js")), name="js")
