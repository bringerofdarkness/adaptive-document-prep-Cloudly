import logging
import time
from sqlalchemy.orm import Session

from app.llm.output_parser import clean_text_value
from app.db.repositories.document_repo import get_latest_document
from app.db.repositories.session_repo import (
    create_prep_session_with_questions,
    submit_answers_for_session,
)
from app.llm.mcq_generator import generate_mcqs
from app.retrieval.retriever import retrieve_chunks_for_sections
from app.services.adaptation_service import build_adaptation_payload
from app.db.models import WeakTopicStat

logger = logging.getLogger(__name__)

def _clean_options(options: dict) -> dict[str, str]:
    return {
        str(key): clean_text_value(value)
        for key, value in options.items()
    }

def _chunk_sections(sections: list[int], batch_size: int = 3) -> list[list[int]]:
    return [sections[i : i + batch_size] for i in range(0, len(sections), batch_size)]

def start_interactive_prep_session(
    db: Session,
    selected_section_numbers: list[int],
    questions_per_section: int,
) -> dict:
    document = get_latest_document(db)
    if document is None:
        raise ValueError("No document found. Run ingestion first.")

    adaptation_payload = build_adaptation_payload(
        db=db,
        document_id=document.id,
        selected_section_numbers=selected_section_numbers,
    )

    section_batches = _chunk_sections(selected_section_numbers, batch_size=3)
    compiled_questions = []

    for index, current_batch in enumerate(section_batches):
        for section_num in current_batch:
            
            weak_stats = (
                db.query(WeakTopicStat)
                .filter(
                    WeakTopicStat.document_id == document.id,
                    WeakTopicStat.section_number == section_num,
                    WeakTopicStat.weakness_score > 0.0
                )
                .order_by(WeakTopicStat.weakness_score.desc())
                .all()
            )
            
            if weak_stats:
                weak_topics = [stat.topic for stat in weak_stats]
                search_query = f"Focus heavily on generating MCQs for verified weak topics: {', '.join(weak_topics)}."
            else:
                search_query = "Generate foundational baseline competency MCQs."

            retrieved_chunks = retrieve_chunks_for_sections(
                db=db,
                document=document,
                selected_section_numbers=[section_num],
                query=search_query,
                limit=questions_per_section * 3,
            )

            mcq_sub_set = generate_mcqs(
                retrieved_chunks=retrieved_chunks,
                selected_section_numbers=[section_num],
                questions_per_section=questions_per_section,
                adaptation_payload=adaptation_payload,
            )
            
            if mcq_sub_set and hasattr(mcq_sub_set, 'questions'):
                compiled_questions.extend(mcq_sub_set.questions)

        if index < len(section_batches) - 1:
            time.sleep(0.5)

    class CompiledMCQContainer:
        def __init__(self, questions):
            self.questions = questions

    unified_mcq_set = CompiledMCQContainer(questions=compiled_questions)

    session = create_prep_session_with_questions(
        db=db,
        document_id=document.id,
        selected_section_numbers=selected_section_numbers,
        mode=adaptation_payload["mode"],
        mcq_set=unified_mcq_set,
        adaptation_payload=adaptation_payload,
        adaptation_summary=adaptation_payload["summary"],
    )

    return {
        "session_id": session.id,
        "document_id": document.id,
        "mode": session.mode,
        "selected_sections": selected_section_numbers,
        "total_questions": session.total_questions,
        "adaptation_summary": session.adaptation_summary,
        "questions": [
            {
                "question_id": question.question_id,
                "section_number": question.section_number,
                "topic": clean_text_value(question.topic),
                "difficulty": question.difficulty,
                "question": clean_text_value(question.question),
                "options": _clean_options(dict(question.options)),
                "adaptation_reason": clean_text_value(question.adaptation_reason),
            }
            for question in compiled_questions
        ],
    }

def submit_interactive_prep_answers(
    db: Session,
    session_id: str,
    answers: dict[str, str],
) -> dict:
    return submit_answers_for_session(
        db=db,
        session_id=session_id,
        answer_map=answers,
    )