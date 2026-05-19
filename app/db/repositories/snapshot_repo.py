from sqlalchemy.orm import Session

from app.db.models import KBSnapshot


def save_kb_snapshot(
    db: Session,
    session_id: str,
    snapshot_json: dict,
) -> KBSnapshot:
    snapshot = KBSnapshot(
        session_id=session_id,
        snapshot_json=snapshot_json,
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return snapshot