from sqlalchemy.orm import Session

from app.db.models import GeneratedQuestion, PrepSession, UserAnswer, WeakTopicStat


def build_adaptation_payload(
    db: Session,
    document_id: str,
    selected_section_numbers: list[int],
) -> dict:
    """
    Build compact behavioral context for adaptive MCQ generation.

    This avoids sending raw history dumps to the LLM.
    """
    prior_sessions = (
        db.query(PrepSession)
        .filter(PrepSession.document_id == document_id)
        .all()
    )

    relevant_sessions = [
        session
        for session in prior_sessions
        if set(session.selected_section_numbers).intersection(selected_section_numbers)
    ]

    weak_stats = (
        db.query(WeakTopicStat)
        .filter(
            WeakTopicStat.document_id == document_id,
            WeakTopicStat.section_number.in_(selected_section_numbers),
            WeakTopicStat.wrong_count > 0,
        )
        .order_by(
            WeakTopicStat.weakness_score.desc(),
            WeakTopicStat.wrong_count.desc(),
            WeakTopicStat.last_seen_at.desc(),
        )
        .limit(10)
        .all()
    )

    mastered_questions = (
        db.query(GeneratedQuestion)
        .join(UserAnswer, UserAnswer.question_id == GeneratedQuestion.id)
        .filter(
            GeneratedQuestion.document_id == document_id,
            GeneratedQuestion.section_number.in_(selected_section_numbers),
            UserAnswer.is_correct.is_(True),
        )
        .order_by(GeneratedQuestion.created_at.desc())
        .limit(10)
        .all()
    )

    previous_wrong_questions = (
        db.query(GeneratedQuestion)
        .join(UserAnswer, UserAnswer.question_id == GeneratedQuestion.id)
        .filter(
            GeneratedQuestion.document_id == document_id,
            GeneratedQuestion.section_number.in_(selected_section_numbers),
            UserAnswer.is_correct.is_(False),
        )
        .order_by(GeneratedQuestion.created_at.desc())
        .limit(10)
        .all()
    )

    is_returning_run = len(relevant_sessions) > 0

    weak_topics = [
        {
            "section_number": stat.section_number,
            "topic": stat.topic,
            "attempts": stat.attempts,
            "wrong_count": stat.wrong_count,
            "correct_count": stat.correct_count,
            "weakness_score": stat.weakness_score,
        }
        for stat in weak_stats
    ]

    mastered_question_texts = [
        question.question_text
        for question in mastered_questions
    ]

    previous_wrong_question_texts = [
        question.question_text
        for question in previous_wrong_questions
    ]

    if is_returning_run and weak_topics:
        summary = (
            "Adaptive run: prior history found. Focus more on weak topics "
            "and avoid excessive repetition of mastered questions."
        )
    elif is_returning_run:
        summary = (
            "Adaptive run: prior history found, but no repeated weak topics yet. "
            "Generate fresh coverage while avoiding mastered repetition."
        )
    else:
        summary = "Cold-start run: no prior relevant history found."

    return {
        "is_returning_run": is_returning_run,
        "mode": "adaptive" if is_returning_run else "cold_start",
        "relevant_prior_session_count": len(relevant_sessions),
        "weak_topics": weak_topics,
        "mastered_question_texts": mastered_question_texts,
        "previous_wrong_question_texts": previous_wrong_question_texts,
        "summary": summary,
    }