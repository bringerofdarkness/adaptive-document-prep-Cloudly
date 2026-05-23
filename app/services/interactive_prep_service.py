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

logger = logging.getLogger(__name__)

def _clean_options(options: dict) -> dict[str, str]:
    return {
        str(key): clean_text_value(value)
        for key, value in options.items()
    }

def _chunk_sections(sections: list[int], batch_size: int = 3) -> list[list[int]]:
    """Helper utility to divide target section arrays into smaller, optimized evaluation batches."""
    return [sections[i : i + batch_size] for i in range(0, len(sections), batch_size)]

def start_interactive_prep_session(
    db: Session,
    selected_section_numbers: list[int],
    questions_per_section: int,
) -> dict:
    document = get_latest_document(db)

    if document is None:
        raise ValueError("No document found. Run ingestion first.")

    # 1. Compute state adaptation data once globally
    adaptation_payload = build_adaptation_payload(
        db=db,
        document_id=document.id,
        selected_section_numbers=selected_section_numbers,
    )

    # 2. Slice target sections into parallelizable batches (e.g., max 3 sections per network trip)
    section_batches = _chunk_sections(selected_section_numbers, batch_size=3)
    compiled_questions = []

    logger.info(f"Optimizing latency: Split {len(selected_section_numbers)} sections into {len(section_batches)} execution batches.")

    # 3. Process batches sequentially to mitigate Groq Free-Tier concurrent burst locking
    for index, current_batch in enumerate(section_batches):
        logger.info(f"Processing execution batch {index + 1}/{len(section_batches)} for sections: {current_batch}")
        
        # Pull vector chunks isolated directly to the active processing batch context
        retrieved_chunks = retrieve_chunks_for_sections(
            db=db,
            document=document,
            selected_section_numbers=current_batch,
            query="Generate MCQs from the selected sections.",
            limit=max(len(current_batch), len(current_batch) * questions_per_section),
        )

        # Generate specific segment questions via LLM context
        mcq_sub_set = generate_mcqs(
            retrieved_chunks=retrieved_chunks,
            selected_section_numbers=current_batch,
            questions_per_section=questions_per_section,
            adaptation_payload=adaptation_payload,
        )
        
        # Accumulate objects safely out of internal container models
        if mcq_sub_set and hasattr(mcq_sub_set, 'questions'):
            compiled_questions.extend(mcq_sub_set.questions)

        # Strategic Politeness Backoff: Mitigates Groq API HTTP 429 locks during heavy loops
        if index < len(section_batches) - 1:
            logger.info("Enforcing token safety window. Sleeping for 2.5 seconds...")
            time.sleep(2.5)

    # 4. Reconstruct uniform container to feed into state tracking and repository layers
    # We create a dummy container object mimicking the expected structure of mcq_set for database ingestion
    class CompiledMCQContainer:
        def __init__(self, questions):
            self.questions = questions

    unified_mcq_set = CompiledMCQContainer(questions=compiled_questions)

    # 5. Commit state tracking details down to relational databases
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