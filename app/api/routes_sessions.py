from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import GeneratedQuestion, PrepSession, UserAnswer
from app.db.session import get_db
from app.schemas.session import SessionSummaryResponse


router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionSummaryResponse])
def list_sessions(
    db: Session = Depends(get_db),
) -> list[SessionSummaryResponse]:
    sessions = (
        db.query(PrepSession)
        .order_by(PrepSession.created_at.desc())
        .limit(25)
        .all()
    )

    return [
        SessionSummaryResponse(
            session_id=session.id,
            document_id=session.document_id,
            mode=session.mode,
            selected_sections=session.selected_section_numbers,
            score=session.score,
            total_questions=session.total_questions,
            correct_count=session.correct_count,
            wrong_count=session.wrong_count,
            adaptation_summary=session.adaptation_summary,
            created_at=session.created_at.isoformat(),
        )
        for session in sessions
    ]


@router.get("/{session_id}")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
) -> dict:
    session = db.query(PrepSession).filter(PrepSession.id == session_id).first()

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    questions = (
        db.query(GeneratedQuestion)
        .filter(GeneratedQuestion.session_id == session.id)
        .order_by(GeneratedQuestion.created_at.asc())
        .all()
    )

    question_records = []

    for question in questions:
        answer = (
            db.query(UserAnswer)
            .filter(UserAnswer.question_id == question.id)
            .first()
        )

        question_records.append(
            {
                "question_id": question.id,
                "section_number": question.section_number,
                "topic": question.topic,
                "difficulty": question.difficulty,
                "question": question.question_text,
                "options": question.options,
                "correct_answer": question.correct_answer,
                "user_answer": answer.selected_answer if answer else None,
                "is_correct": answer.is_correct if answer else None,
                "explanation": question.explanation,
                "adaptation_reason": question.adaptation_reason,
            }
        )

    return {
        "session_id": session.id,
        "document_id": session.document_id,
        "mode": session.mode,
        "selected_sections": session.selected_section_numbers,
        "score": session.score,
        "total_questions": session.total_questions,
        "correct_count": session.correct_count,
        "wrong_count": session.wrong_count,
        "adaptation_summary": session.adaptation_summary,
        "adaptation_payload": session.adaptation_payload,
        "created_at": session.created_at.isoformat(),
        "questions": question_records,
    }