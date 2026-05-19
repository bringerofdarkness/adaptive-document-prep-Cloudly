from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_documents import router as documents_router
from app.api.routes_prep import router as prep_router
from app.api.routes_sessions import router as sessions_router
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend API for adaptive PDF-based MCQ preparation.",
)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(prep_router)
app.include_router(sessions_router)
