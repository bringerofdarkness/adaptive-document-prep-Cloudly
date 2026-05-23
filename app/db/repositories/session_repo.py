from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import GeneratedQuestion, KBSnapshot, PrepSession, UserAnswer, WeakTopicStat
from app.schemas.question import MCQSet

VALID_ANSWER_KEYS = {"A", "B", "C", "D"}


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
    stat.last_seen_at = datetime.now(timezone.utc).replace(tzinfo=None)


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
    meta_payload = dict(adaptation_payload or {})
    
    if "telemetry" in scoring_payload:
        meta_payload["telemetry"] = scoring_payload["telemetry"]
    else:
        meta_payload["telemetry"] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cached_applied": False
        }

    session = PrepSession(
        document_id=document_id,
        mode=mode,
        selected_section_numbers=selected_section_numbers,
        score=scoring_payload["score"],
        total_questions=scoring_payload["total_questions"],
        correct_count=scoring_payload["correct_count"],
        wrong_count=scoring_payload["wrong_count"],
        adaptation_payload=meta_payload,
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


def create_prep_session_with_questions(
    db: Session,
    document_id: str,
    selected_section_numbers: list[int],
    mode: str,
    mcq_set: MCQSet,
    adaptation_payload: dict | None = None,
    adaptation_summary: str | None = None,
) -> PrepSession:
    session = PrepSession(
        document_id=document_id,
        mode=mode,
        selected_section_numbers=selected_section_numbers,
        score=0.0,
        total_questions=len(mcq_set.questions),
        correct_count=0,
        wrong_count=0,
        adaptation_payload=adaptation_payload or {},
        adaptation_summary=adaptation_summary,
    )

    db.add(session)
    db.flush()

    for question in mcq_set.questions:
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

    db.commit()
    db.refresh(session)

    return session


def submit_answers_for_session(
    db: Session,
    session_id: str,
    answer_map: dict[str, str],
) -> dict:
    session = db.query(PrepSession).filter(PrepSession.id == session_id).first()

    if session is None:
        raise ValueError(f"Session not found: {session_id}")

    existing_answer_count = (
        db.query(UserAnswer)
        .filter(UserAnswer.session_id == session_id)
        .count()
    )

    if existing_answer_count > 0:
        raise ValueError("Answers have already been submitted for this session.")

    questions = (
        db.query(GeneratedQuestion)
        .filter(GeneratedQuestion.session_id == session_id)
        .order_by(GeneratedQuestion.created_at.asc())
        .all()
    )

    if not questions:
        raise ValueError("No questions found for this session.")

    missing_question_ids = [
        question.id
        for question in questions
        if question.id not in answer_map
    ]

    if missing_question_ids:
        raise ValueError(f"Missing answers for questions: {missing_question_ids}")

    results = []
    correct_count = 0

    for question in questions:
        selected_answer = str(answer_map[question.id]).strip().upper()

        if selected_answer not in VALID_ANSWER_KEYS:
            raise ValueError(f"Invalid answer for question_id={question.id}")

        is_correct = selected_answer == question.correct_answer

        if is_correct:
            correct_count += 1

        clarification = None if is_correct else question.explanation

        db.add(
            UserAnswer(
                session_id=session.id,
                question_id=question.id,
                selected_answer=selected_answer,
                correct_answer=question.correct_answer,
                is_correct=is_correct,
                clarification=clarification,
            )
        )

        _update_weak_topic_stat(
            db=db,
            document_id=session.document_id,
            section_number=question.section_number,
            topic=question.topic,
            is_correct=is_correct,
        )

        results.append(
            {
                "question_id": question.id,
                "section_number": question.section_number,
                "topic": question.topic,
                "selected_answer": selected_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "clarification": clarification,
            }
        )

    total_questions = len(questions)
    wrong_count = total_questions - correct_count

    session.total_questions = total_questions
    session.correct_count = correct_count
    session.wrong_count = wrong_count
    session.score = round((correct_count / total_questions) * 100, 2)

    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "score": session.score,
        "total_questions": session.total_questions,
        "correct_count": session.correct_count,
        "wrong_count": session.wrong_count,
        "results": results,
    }