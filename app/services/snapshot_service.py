import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import GeneratedQuestion, PrepSession, UserAnswer, WeakTopicStat
from app.db.repositories.snapshot_repo import save_kb_snapshot


def build_kb_snapshot(
    db: Session,
    current_session_id: str,
    limit: int = 5,
) -> dict:
    recent_sessions = (
        db.query(PrepSession)
        .order_by(PrepSession.created_at.desc())
        .limit(limit)
        .all()
    )

    session_records = []

    for session in recent_sessions:
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
                    "user_answer": answer.selected_answer if answer else None,
                    "correct_answer": question.correct_answer,
                    "is_correct": answer.is_correct if answer else None,
                    "clarification": answer.clarification if answer else None,
                    "adaptation_reason": question.adaptation_reason,
                    "source_chunk_ids": question.source_chunk_ids,
                }
            )

        weak_topics = (
            db.query(WeakTopicStat)
            .filter(
                WeakTopicStat.document_id == session.document_id,
                WeakTopicStat.section_number.in_(session.selected_section_numbers),
            )
            .order_by(
                WeakTopicStat.weakness_score.desc(),
                WeakTopicStat.wrong_count.desc(),
                WeakTopicStat.last_seen_at.desc(),
            )
            .limit(10)
            .all()
        )

        session_records.append(
            {
                "session_id": session.id,
                "timestamp": session.created_at.isoformat(),
                "mode": session.mode,
                "selected_sections": session.selected_section_numbers,
                "score": session.score,
                "total_questions": session.total_questions,
                "correct_count": session.correct_count,
                "wrong_count": session.wrong_count,
                "adaptation_summary": session.adaptation_summary,
                "adaptation_payload": session.adaptation_payload,
                "questions_asked": question_records,
                "weak_topics": [
                    {
                        "section_number": stat.section_number,
                        "topic": stat.topic,
                        "attempts": stat.attempts,
                        "wrong_count": stat.wrong_count,
                        "correct_count": stat.correct_count,
                        "weakness_score": stat.weakness_score,
                    }
                    for stat in weak_topics
                ],
            }
        )

    return {
        "snapshot_created_at": datetime.utcnow().isoformat(),
        "current_session_id": current_session_id,
        "recent_session_count": len(session_records),
        "recent_sessions": session_records,
    }


def save_and_export_kb_snapshot(
    db: Session,
    current_session_id: str,
    output_path: str | Path,
) -> dict:
    snapshot_json = build_kb_snapshot(
        db=db,
        current_session_id=current_session_id,
    )

    save_kb_snapshot(
        db=db,
        session_id=current_session_id,
        snapshot_json=snapshot_json,
    )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(snapshot_json, indent=2),
        encoding="utf-8",
    )

    return snapshot_json