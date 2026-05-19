from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import GeneratedQuestion, KBSnapshot, PrepSession, UserAnswer, WeakTopicStat
from app.schemas.question import MCQSet


def _update_weak_topic_stat(
    db: Session,
    document_id: str,
    section_number: int,
    topic: str,
    is_correct: bool,
) -> None:
    stat = (
        db.query(WeakTopicStat)
        .filter(
            WeakTopicStat.document_id == document_id,
            WeakTopicStat.section_number == section_number,
            WeakTopicStat.topic == topic,
        )
        .first()
    )

    if stat is None:
        stat = WeakTopicStat(
            document_id=document_id,
            section_number=section_number,
            topic=topic,
        )
        db.add(stat)
        db.flush()

    stat.attempts += 1

    if is_correct:
        stat.correct_count += 1
    else:
        stat.wrong_count += 1

    stat.weakness_score = round(stat.wrong_count / stat.attempts, 4)
    stat.last_seen_at = datetime.utcnow()


def create_prep_session_with_results(
    db: Session,
    document_id: str,
    selected_section_numbers: list[int],
    mode: str,
    mcq_set: MCQSet,
    scoring_payload: dict,
    adaptation_payload: dict | None = None,
    adaptation_summary: str | None = None,
) -> PrepSession:
    session = PrepSession(
        document_id=document_id,
        mode=mode,
        selected_section_numbers=selected_section_numbers,
        score=scoring_payload["score"],
        total_questions=scoring_payload["total_questions"],
        correct_count=scoring_payload["correct_count"],
        wrong_count=scoring_payload["wrong_count"],
        adaptation_payload=adaptation_payload or {},
        adaptation_summary=adaptation_summary,
    )

    db.add(session)
    db.flush()

    results_by_question_id = {
        item["question_id"]: item
        for item in scoring_payload["results"]
    }

    for question in mcq_set.questions:
        result = results_by_question_id[question.question_id]

        question_row = GeneratedQuestion(
            id=question.question_id,
            session_id=session.id,
            document_id=document_id,
            section_id=question.section_id,
            section_number=question.section_number,
            topic=question.topic,
            difficulty=question.difficulty,
            question_text=question.question,
            options=dict(question.options),
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            adaptation_reason=question.adaptation_reason,
            source_chunk_ids=question.source_chunk_ids,
        )

        db.add(question_row)
        db.flush()

        answer_row = UserAnswer(
            session_id=session.id,
            question_id=question_row.id,
            selected_answer=result["selected_answer"],
            correct_answer=result["correct_answer"],
            is_correct=result["is_correct"],
            clarification=result["clarification"],
        )

        db.add(answer_row)

        _update_weak_topic_stat(
            db=db,
            document_id=document_id,
            section_number=question.section_number,
            topic=question.topic,
            is_correct=result["is_correct"],
        )

    db.commit()
    db.refresh(session)

    return session

def clear_prep_history_for_document(
    db: Session,
    document_id: str,
) -> None:
    session_ids = [
        row.id
        for row in db.query(PrepSession.id)
        .filter(PrepSession.document_id == document_id)
        .all()
    ]

    if not session_ids:
        return

    db.query(KBSnapshot).filter(KBSnapshot.session_id.in_(session_ids)).delete(
        synchronize_session=False
    )
    db.query(UserAnswer).filter(UserAnswer.session_id.in_(session_ids)).delete(
        synchronize_session=False
    )
    db.query(GeneratedQuestion).filter(
        GeneratedQuestion.session_id.in_(session_ids)
    ).delete(synchronize_session=False)
    db.query(PrepSession).filter(PrepSession.id.in_(session_ids)).delete(
        synchronize_session=False
    )
    db.query(WeakTopicStat).filter(WeakTopicStat.document_id == document_id).delete(
        synchronize_session=False
    )

    db.commit()