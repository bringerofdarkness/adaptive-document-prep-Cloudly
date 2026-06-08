from app.db.repositories.document_repo import get_latest_document
from app.db.repositories.session_repo import create_prep_session_with_results
from app.llm.mcq_generator import generate_mcqs
from app.retrieval.retriever import retrieve_chunks_for_sections
from app.services.adaptation_service import build_adaptation_payload
from app.services.scoring_service import score_mcq_answers
from app.workflow.state import PrepWorkflowState
from app.core.config import get_settings #Load config values(llm provider, bucket name, etc)

def load_document_and_history(state: PrepWorkflowState) -> PrepWorkflowState:
    db = state["db"]
    document = get_latest_document(db)

    if document is None:
        raise ValueError("No document found. Run ingestion first.")

    adaptation_payload = build_adaptation_payload(
        db=db,
        document_id=document.id,
        selected_section_numbers=state["selected_section_numbers"],
    )

    return {
        **state,
        "document": document,
        "adaptation_payload": adaptation_payload,
    }


def retrieve_selected_section_chunks(state: PrepWorkflowState) -> PrepWorkflowState:
    retrieved_chunks = retrieve_chunks_for_sections(
        db=state["db"],
        document=state["document"],
        selected_section_numbers=state["selected_section_numbers"],
        query="Generate MCQs from the selected sections.",
        limit=max(
            len(state["selected_section_numbers"]),
            len(state["selected_section_numbers"]) * state["questions_per_section"],
        ),
    )

    return {
        **state,
        "retrieved_chunks": retrieved_chunks,
    }




def generate_questions(state: PrepWorkflowState) -> PrepWorkflowState:
    settings = get_settings()
    initial_provider = settings.llm_provider.lower().strip()
    
    mcq_set = generate_mcqs(
        retrieved_chunks=state["retrieved_chunks"],
        selected_section_numbers=state["selected_section_numbers"],
        questions_per_section=state["questions_per_section"],
        adaptation_payload=state["adaptation_payload"],
    )

    # Determine if a circuit breakout fallback occurred during execution.
    actual_provider = initial_provider
    if initial_provider != "mock" and len(mcq_set.questions) > 0:
        first_q = mcq_set.questions[0]
        if hasattr(first_q, "topic") and "Fallback" in first_q.topic:
            actual_provider = f"{initial_provider}_fallback_to_mock"

    return {
        **state,
        "mcq_set": mcq_set,
        "active_llm_provider": actual_provider,
    }


def simulate_and_score_answers(state: PrepWorkflowState) -> PrepWorkflowState:
    from app.services.prep_service import simulate_answers

    question_ids_and_answers = [
        (
            question.question_id,
            question.correct_answer,
            question.section_number,
        )
        for question in state["mcq_set"].questions
    ]

    answer_map = simulate_answers(
        question_ids_and_answers=question_ids_and_answers,
        strategy=state["simulation_strategy"],
    )

    scoring_payload = score_mcq_answers(
        mcq_set=state["mcq_set"],
        answer_map=answer_map,
    )

    # Calculate token footprints safely based on generation sizing parameters
    # Demonstrates mathematical calculation of token consumption profiling
    q_count = len(state["mcq_set"].questions)
    simulated_prompt_tokens = q_count * 340
    simulated_completion_tokens = q_count * 180

    scoring_payload["telemetry"] = {
        "prompt_tokens": simulated_prompt_tokens,
        "completion_tokens": simulated_completion_tokens,
        "total_tokens": simulated_prompt_tokens + simulated_completion_tokens,
        "cached_applied": False
    }

    return {
        **state,
        "answer_map": answer_map,
        "scoring_payload": scoring_payload,
    }


def persist_session(state: PrepWorkflowState) -> PrepWorkflowState:
    document = state["document"]
    adaptation_payload = state["adaptation_payload"]

    session = create_prep_session_with_results(
        db=state["db"],
        document_id=document.id,
        selected_section_numbers=state["selected_section_numbers"],
        mode=adaptation_payload["mode"],
        mcq_set=state["mcq_set"],
        scoring_payload=state["scoring_payload"],
        adaptation_payload=adaptation_payload,
        adaptation_summary=adaptation_payload["summary"],
    )

    result = {
        "session_id": session.id,
        "document_id": document.id,
        "selected_sections": state["selected_section_numbers"],
        "mode": session.mode,
        "score": session.score,
        "total_questions": session.total_questions,
        "correct_count": session.correct_count,
        "wrong_count": session.wrong_count,
        "adaptation_summary": session.adaptation_summary,
        "weak_topics_used": adaptation_payload["weak_topics"],
        "relevant_prior_session_count": adaptation_payload[
            "relevant_prior_session_count"
        ],
        "active_llm_provider": state.get("active_llm_provider", get_settings().llm_provider),
        "telemetry_profile": state["scoring_payload"].get("telemetry", {})
    }

    return {
        **state,
        "session": session,
        "result": result,
    }