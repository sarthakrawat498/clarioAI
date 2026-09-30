import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, SessionLocal
import app.models  # noqa: F401
from app.api.v1.router import api_v1_router
from app.services.policy_service import seed_policy_catalog
from app.rag.vector_store import vector_store_manager

# Configure Logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown actions."""
    logger.info("Initializing Health Insurance Assistant Backend...")
    # Initialize DB schema
    init_db()
    
    # Seed policy catalogue
    db = SessionLocal()
    try:
        seed_policy_catalog(db)
    finally:
        db.close()

    # Seed ChromaDB vector store
    try:
        vector_store_manager.ingest_all_sample_policies()
    except Exception as e:
        logger.warning(f"ChromaDB initial seeding warning: {e}")

    logger.info("Application startup complete.")
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS with specific origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Mount API V1 Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True, reload_dirs=["app"])

