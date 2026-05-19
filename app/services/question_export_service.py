import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import GeneratedQuestion, PrepSession, UserAnswer


def export_session_questions(
    db: Session,
    session_id: str,
    output_path: str | Path,
) -> dict:
    session = (
        db.query(PrepSession)
        .filter(PrepSession.id == session_id)
        .first()
    )

    if session is None:
        raise ValueError(f"Session not found: {session_id}")

    questions = (
        db.query(GeneratedQuestion)
        .filter(GeneratedQuestion.session_id == session_id)
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
                "section_id": question.section_id,
                "section_number": question.section_number,
                "topic": question.topic,
                "difficulty": question.difficulty,
                "question": question.question_text,
                "options": question.options,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "adaptation_reason": question.adaptation_reason,
                "source_chunk_ids": question.source_chunk_ids,
                "simulated_user_answer": answer.selected_answer if answer else None,
                "is_correct": answer.is_correct if answer else None,
                "clarification": answer.clarification if answer else None,
            }
        )

    payload = {
        "session_id": session.id,
        "mode": session.mode,
        "selected_sections": session.selected_section_numbers,
        "score": session.score,
        "total_questions": session.total_questions,
        "correct_count": session.correct_count,
        "wrong_count": session.wrong_count,
        "adaptation_summary": session.adaptation_summary,
        "adaptation_payload": session.adaptation_payload,
        "questions": question_records,
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    return payload