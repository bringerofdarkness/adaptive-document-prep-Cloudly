import os
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "adaptive_doc_prep_worker",
    broker=settings.redis_url if hasattr(settings, "redis_url") else "redis://localhost:6380/0",
    backend=settings.redis_url if hasattr(settings, "redis_url") else "redis://localhost:6380/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # This forces the app instance to parse your tasks file right away
    imports=["app.workers.tasks"],
)