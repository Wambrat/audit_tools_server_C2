from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.routes import router
from app.logger import setup_logging, get_logger
from app.db import set_db_instance
from app.openapi_config import TAGS_METADATA, INFO, SERVERS
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configurer le logging structuré
setup_logging(app_name="c2-server", log_level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

logger.info("Initializing C2 Server API")

# ===== Configuration de la Base de Données =====
DATABASE_MODE = os.getenv("DATABASE_MODE", "memory").lower()

if DATABASE_MODE == "mongodb":
    try:
        from app.database_mongodb import MongoDatabase
        logger.info("🟢 Database mode: MongoDB (persistent)")
        db_instance = MongoDatabase()
        logger.info("✅ MongoDB connected successfully")
    except Exception as e:
        logger.warning(f"⚠️ MongoDB connection failed: {e}")
        logger.info("📡 Fallback to in-memory database")
        from app.database import Database
        db_instance = Database()
else:
    try:
        from app.database import Database
        logger.info("🟢 Database mode: In-Memory (development)")
        db_instance = Database()
        logger.info("✅ In-Memory database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

# Enregistrer l'instance pour que routes.py et autres modules y accèdent
set_db_instance(db_instance)

# Peupler les commandes/templates système depuis le zip d'archive de modules
if hasattr(db_instance, "seed_default_modules"):
    try:
        seeded = db_instance.seed_default_modules()
        logger.info(f"Seed modules result: {seeded}")
    except Exception as exc:
        logger.warning(f"Default module seeding skipped: {exc}")

# Créer l'application FastAPI avec configuration OpenAPI complète
app = FastAPI(
    title=INFO["title"],
    description=INFO["description"],
    version=INFO["version"],
    contact=INFO["contact"],
    license_info=INFO["license"],
    servers=SERVERS,
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",                  # Swagger UI (standard)
    redoc_url="/redoc",                # ReDoc (standard)
    openapi_url="/openapi.json",       # OpenAPI schema (standard)
)

# ===== Middleware for Payload Size Validation =====
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

MAX_PAYLOAD_SIZE = int(os.getenv("MAX_PAYLOAD_SIZE", 10485760))  # 10 MB default

class PayloadSizeValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate request payload size and prevent DOS attacks"""
    
    async def dispatch(self, request: Request, call_next):
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_PAYLOAD_SIZE:
            logger.warning(
                f"Payload size exceeded: {content_length} bytes (max: {MAX_PAYLOAD_SIZE}) "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            return JSONResponse(
                status_code=413,
                content={"detail": f"Payload too large (max {MAX_PAYLOAD_SIZE} bytes)"}
            )
        return await call_next(request)


# ===== Middleware for Security Headers =====
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # HSTS: Force HTTPS for 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP: Restrict resource loading (prevents XSS)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://unpkg.com https://cdn.jsdelivr.net; "
            "frame-ancestors 'none'"
        )
        
        # X-Frame-Options: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options: Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection: Legacy XSS filter (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy: Control referer leaking
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy: Restrict browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=()"
        )
        
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ===== Middleware CORS =====
# Autoriser explicitement les frontends locaux utilisés par le projet
configured_origins = [origin.strip() for origin in os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5500,http://localhost:8080,http://127.0.0.1:5500,http://127.0.0.1:8000,http://127.0.0.1:8080"
).split(",") if origin.strip()]
origins = list(dict.fromkeys(configured_origins + [
    "http://localhost:3000",
    "http://localhost:5500",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8000",
]))
logger.info(f"Setting up CORS with {len(origins)} allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Routes =====
app.include_router(router)
logger.info("Routes registered successfully")

# ===== Static Files =====
try:
    web_dir = os.path.join(os.path.dirname(__file__), "web")
    if os.path.isdir(web_dir):
        app.mount("/build", StaticFiles(directory=web_dir), name="build")
        logger.info(f"Static files mounted at /build from {web_dir}")
    else:
        logger.warning(f"Web directory not found: {web_dir}")
except Exception as e:
    logger.warning(f"Failed to mount static files: {e}")



@app.get("/")
async def root():
    """Health check"""
    logger.debug("Health check requested")
    return {
        "status": "running",
        "service": "C2 Server API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Endpoint de santé"""
    logger.debug("Health endpoint called")
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Gestionnaire global des exceptions"""
    logger.error(
        f"Unhandled exception: {type(exc).__name__} at {request.method} {request.url} - {str(exc)}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    env = os.getenv("ENV", "development")
    
    logger.info(
        f"Starting C2 Server API on {host}:{port} (environment: {env})"
    )
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=env == "development"
    )
