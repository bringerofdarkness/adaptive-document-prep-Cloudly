import os
from celery import Celery


BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6380/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6380/0")

celery_app = Celery(
    "adaptive_doc_tasks",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.background.tasks"] 
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Dhaka",
    enable_utc=True,
)