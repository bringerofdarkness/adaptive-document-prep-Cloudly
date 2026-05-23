import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from app.db.session import get_db
from app.core.celery_app import celery_app  # Imported cleanly to handle dynamic task sending
from app.schemas.prep import (
    PrepStartRequest,
    PrepSubmitRequest,
    PrepSubmitResponse,
    TaskStatusResponse,
)
from app.services.interactive_prep_service import (
    submit_interactive_prep_answers,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prep", tags=["prep"])


@router.post("/start", status_code=202)
def start_prep(request: PrepStartRequest) -> dict:
    """
    Triggers the generation pipeline asynchronously in the Celery worker pool, 
    instantly shedding read-blocking latency away from the primary thread.
    """
    try:
        # send_task routes the execution payload to Redis using the explicit task name string.
        # This completely breaks the circular startup lock and prevents local import failures.
        task = celery_app.send_task(
            "app.workers.tasks.async_start_prep_session",
            kwargs={
                "selected_section_numbers": request.selected_section_numbers,
                "questions_per_section": request.questions_per_section,
            }
        )
    except Exception as error:
        logger.error(f"Failed to route task to Celery broker: {str(error)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue task broker: {str(error)}")

    # Return 202 Accepted status metadata immediately with tracking token
    return {
        "task_id": task.id,
        "status": "QUEUED",
        "message": "Adaptive generation pipeline initiated successfully in background thread workers."
    }


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Polled endpoint allowing the UI client to check task processing states 
    and pull down generated results once the worker yields SUCCESS.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.status == "SUCCESS":
        response["result"] = task_result.result
    elif task_result.status == "FAILURE":
        response["result"] = {"error": str(task_result.info)}
        
    return TaskStatusResponse(**response)


@router.post("/submit", response_model=PrepSubmitResponse)
def submit_prep(
    request: PrepSubmitRequest,
    db: Session = Depends(get_db),
) -> PrepSubmitResponse:
    """
    Submits answers for evaluation against the generated session payload.
    """
    try:
        result = submit_interactive_prep_answers(
            db=db,
            session_id=request.session_id,
            answers=request.answers,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return PrepSubmitResponse(**result)