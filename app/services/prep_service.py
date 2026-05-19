from sqlalchemy.orm import Session

from app.db.repositories.document_repo import get_latest_document
from app.db.repositories.session_repo import create_prep_session_with_results
from app.llm.mcq_generator import generate_mock_mcqs
from app.retrieval.retriever import retrieve_chunks_for_sections
from app.services.adaptation_service import build_adaptation_payload
from app.services.scoring_service import score_mcq_answers


def _wrong_answer(correct_answer: str) -> str:
    for option in ["A", "B", "C", "D"]:
        if option != correct_answer:
            return option

    return "A"


def simulate_answers(
    question_ids_and_answers: list[tuple[str, str, int]],
    strategy: str,
) -> dict[str, str]:
    """
    Strategies:
    - section8_weak: answer section 8 incorrectly, others correctly.
    - alternating: alternate correct/wrong.
    - all_correct: all answers correct.
    """
    answer_map = {}

    for index, (question_id, correct_answer, section_number) in enumerate(
        question_ids_and_answers,
        start=1,
    ):
        should_be_wrong = False

        if strategy == "section8_weak":
            should_be_wrong = section_number == 8
        elif strategy == "alternating":
            should_be_wrong = index % 2 == 0
        elif strategy == "all_correct":
            should_be_wrong = False
        else:
            raise ValueError(f"Unknown simulation strategy: {strategy}")

        answer_map[question_id] = (
            _wrong_answer(correct_answer) if should_be_wrong else correct_answer
        )

    return answer_map


def run_mock_prep_session(
    db: Session,
    selected_section_numbers: list[int],
    questions_per_section: int = 2,
    simulation_strategy: str = "section8_weak",
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
        limit=max(12, len(selected_section_numbers) * questions_per_section * 3),
    )

    mcq_set = generate_mock_mcqs(
        retrieved_chunks=retrieved_chunks,
        selected_section_numbers=selected_section_numbers,
        questions_per_section=questions_per_section,
        adaptation_payload=adaptation_payload,
    )

    question_ids_and_answers = [
        (
            question.question_id,
            question.correct_answer,
            question.section_number,
        )
        for question in mcq_set.questions
    ]

    answer_map = simulate_answers(
        question_ids_and_answers=question_ids_and_answers,
        strategy=simulation_strategy,
    )

    scoring_payload = score_mcq_answers(
        mcq_set=mcq_set,
        answer_map=answer_map,
    )

    session = create_prep_session_with_results(
        db=db,
        document_id=document.id,
        selected_section_numbers=selected_section_numbers,
        mode=adaptation_payload["mode"],
        mcq_set=mcq_set,
        scoring_payload=scoring_payload,
        adaptation_payload=adaptation_payload,
        adaptation_summary=adaptation_payload["summary"],
    )

    return {
        "session_id": session.id,
        "document_id": document.id,
        "selected_sections": selected_section_numbers,
        "mode": session.mode,
        "score": session.score,
        "total_questions": session.total_questions,
        "correct_count": session.correct_count,
        "wrong_count": session.wrong_count,
        "adaptation_summary": session.adaptation_summary,
        "weak_topics_used": adaptation_payload["weak_topics"],
        "relevant_prior_session_count": adaptation_payload["relevant_prior_session_count"],
    }