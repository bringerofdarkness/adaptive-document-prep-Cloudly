from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prep import PrepRunRequest, PrepRunResponse
from app.services.prep_service import run_prep_session


router = APIRouter(prefix="/prep", tags=["prep"])


@router.post("/run-simulated", response_model=PrepRunResponse)
def run_simulated_prep(
    request: PrepRunRequest,
    db: Session = Depends(get_db),
) -> PrepRunResponse:
    result = run_prep_session(
        db=db,
        selected_section_numbers=request.selected_section_numbers,
        questions_per_section=request.questions_per_section,
        simulation_strategy=request.simulation_strategy,
    )

    return PrepRunResponse(**result)