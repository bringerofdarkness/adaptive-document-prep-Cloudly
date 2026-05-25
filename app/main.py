from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes_kb import router as kb_router
from app.api.routes_health import router as health_router
from app.api.routes_documents import router as documents_router
from app.api.routes_prep import router as prep_router
from app.api.routes_sessions import router as sessions_router
from app.core.config import get_settings
from app.core.minio_client import init_minio_storage

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown lifecycle events.
    Guarantees storage infrastructure layers are ready before receiving traffic.
    """
    # 🚀 Startup Lifecycle Phase
    init_minio_storage()
    yield
    # 🛑 Shutdown Lifecycle Phase (Add connection cleanups here if necessary)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend API for adaptive PDF-based MCQ preparation.",
    lifespan=lifespan,
)

# Route Registrations
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(prep_router)
app.include_router(sessions_router)
app.include_router(kb_router)