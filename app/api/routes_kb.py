from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import PrepSession
from app.db.session import get_db
from app.services.snapshot_service import build_kb_snapshot


router = APIRouter(prefix="/kb", tags=["knowledge-base"])


@router.get("/snapshot")
def get_kb_snapshot(
    db: Session = Depends(get_db),
) -> dict:
    latest_session = (
        db.query(PrepSession)
        .order_by(PrepSession.created_at.desc())
        .first()
    )

    if latest_session is None:
        raise HTTPException(status_code=404, detail="No prep session found.")

    return build_kb_snapshot(
        db=db,
        current_session_id=latest_session.id,
    )