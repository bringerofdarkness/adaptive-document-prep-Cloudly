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

def _clean_options(options: dict) -> dict[str, str]:
    return {
        str(key): clean_text_value(value)
        for key, value in options.items()
    }

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

    retrieved_chunks = retrieve_chunks_for_sections(
        db=db,
        document=document,
        selected_section_numbers=selected_section_numbers,
        query="Generate MCQs from the selected sections.",
        limit=max(
            len(selected_section_numbers),
            len(selected_section_numbers) * questions_per_section,
        ),
    )

    mcq_set = generate_mcqs(
        retrieved_chunks=retrieved_chunks,
        selected_section_numbers=selected_section_numbers,
        questions_per_section=questions_per_section,
        adaptation_payload=adaptation_payload,
    )

    session = create_prep_session_with_questions(
        db=db,
        document_id=document.id,
        selected_section_numbers=selected_section_numbers,
        mode=adaptation_payload["mode"],
        mcq_set=mcq_set,
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
    for question in mcq_set.questions
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