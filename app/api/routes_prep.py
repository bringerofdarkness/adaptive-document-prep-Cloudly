from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prep import (
    PrepStartRequest,
    PrepStartResponse,
    PrepSubmitRequest,
    PrepSubmitResponse,
)
from app.services.interactive_prep_service import (
    start_interactive_prep_session,
    submit_interactive_prep_answers,
)


router = APIRouter(prefix="/prep", tags=["prep"])


@router.post("/start", response_model=PrepStartResponse)
def start_prep(
    request: PrepStartRequest,
    db: Session = Depends(get_db),
) -> PrepStartResponse:
    try:
        result = start_interactive_prep_session(
            db=db,
            selected_section_numbers=request.selected_section_numbers,
            questions_per_section=request.questions_per_section,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return PrepStartResponse(**result)


@router.post("/submit", response_model=PrepSubmitResponse)
def submit_prep(
    request: PrepSubmitRequest,
    db: Session = Depends(get_db),
) -> PrepSubmitResponse:
    try:
        result = submit_interactive_prep_answers(
            db=db,
            session_id=request.session_id,
            answers=request.answers,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return PrepSubmitResponse(**result)