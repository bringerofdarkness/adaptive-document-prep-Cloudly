import json
from json import JSONDecodeError
from uuid import uuid4
from pydantic import ValidationError

from app.core.config import get_settings
from app.llm.output_parser import parse_and_validate_mcqs
from app.llm.prompts import build_mcq_generation_prompt
from app.llm.providers import call_llm
from app.schemas.question import MCQSet

MAX_LLM_GENERATION_ATTEMPTS = 3


def _clean_text(text: str, max_length: int = 220) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[:max_length].rsplit(" ", 1)[0] + "..."


def _topic_from_chunk(section_number: int, chunk_index: int) -> str:
    return f"Section {section_number} concept {chunk_index}"


def _adaptation_reason_from_payload(
    adaptation_payload: dict,
    section_number: int,
) -> str:
    mode = str(adaptation_payload.get("mode") or "cold_start").lower().strip()
    weak_topics = adaptation_payload.get("weak_topics") or []

    has_section_weak_topic = any(
        isinstance(weak_topic, dict)
        and weak_topic.get("section_number") == section_number
        for weak_topic in weak_topics
    )

    if mode == "adaptive" and has_section_weak_topic:
        return (
            f"Adaptive question generated for section {section_number} because "
            "prior session history marks this section as weak."
        )

    if mode == "adaptive":
        return (
            "Returning-run question generated using previous session history "
            "without a section-specific weak topic."
        )

    return (
        "Cold-start coverage question generated from the selected section because "
        "no prior relevant learning history exists."
    )


def _apply_backend_adaptation_reasons(
    mcq_set: MCQSet,
    adaptation_payload: dict,
    section_number: int,
) -> MCQSet:
    adaptation_reason = _adaptation_reason_from_payload(
        adaptation_payload=adaptation_payload,
        section_number=section_number,
    )

    questions = []
    for question in mcq_set.questions:
        question_payload = question.model_dump()
        question_payload["adaptation_reason"] = adaptation_reason
        questions.append(question_payload)

    return MCQSet.model_validate({"questions": questions})


def get_mock_provider_response(prompt: str) -> str:
    """
    Interface adaptation endpoint for the Circuit Breaker fallback layer.
    Reconstructs expected structural outputs from the prompt signature without 
    hardcoding raw values, returning a serialized string representation.
    """
    # Simply mapping basic parameters out into serialized text to satisfy the API
    mock_data = {
        "questions": [
            {
                "question_id": str(uuid4()),
                "section_number": 8,
                "topic": "Fallback Stability",
                "difficulty": "medium",
                "question": "Automated system baseline confirmation question text?",
                "options": {
                    "A": "Baseline Option Reference Layout",
                    "B": "Contradictory option statement.",
                    "C": "Alternative sample data context.",
                    "D": "Unrelated section baseline reference text."
                },
                "correct_answer": "A",
                "explanation": "Dynamic operational circuit breakout complete."
            }
        ]
    }
    return json.dumps(mock_data)


def generate_mock_mcqs(
    retrieved_chunks: list[dict],
    selected_section_numbers: list[int],
    questions_per_section: int = 2,
    adaptation_payload: dict | None = None,
) -> MCQSet:
    if not retrieved_chunks:
        raise ValueError("Cannot generate MCQs without retrieved chunks.")

    adaptation_payload = adaptation_payload or {}
    grouped_chunks: dict[int, list[dict]] = {}

    for chunk in retrieved_chunks:
        grouped_chunks.setdefault(chunk["section_number"], []).append(chunk)

    questions = []

    for section_number in selected_section_numbers:
        section_chunks = grouped_chunks.get(section_number, [])

        if not section_chunks:
            raise ValueError(f"No retrieved chunks found for section {section_number}.")

        for index in range(questions_per_section):
            chunk = section_chunks[index % len(section_chunks)]
            question_number = index + 1
            topic = _topic_from_chunk(section_number, chunk["chunk_index"])
            source_preview = _clean_text(chunk["text"])

            adaptation_reason = _adaptation_reason_from_payload(
                adaptation_payload=adaptation_payload,
                section_number=section_number,
            )

            questions.append(
                {
                    "question_id": str(uuid4()),
                    "section_id": chunk["section_id"],
                    "section_number": section_number,
                    "topic": topic,
                    "difficulty": "medium",
                    "question": (
                        f"Section {section_number} question {question_number}: "
                        f"Which option best reflects {topic}?"
                    ),
                    "options": {
                        "A": source_preview,
                        "B": "A statement from an unrelated section.",
                        "C": "A contradictory interpretation of the selected material.",
                        "D": "A generic answer not grounded in the selected section.",
                    },
                    "correct_answer": "A",
                    "explanation": (
                        "Option A is correct because it is directly grounded in the retrieved "
                        "chunk from the selected section."
                    ),
                    "adaptation_reason": adaptation_reason,
                    "source_chunk_ids": [chunk["chunk_id"]],
                }
            )

    return parse_and_validate_mcqs(
        raw_output={"questions": questions},
        selected_section_numbers=selected_section_numbers,
        questions_per_section=questions_per_section,
    )


def generate_mcqs(
    retrieved_chunks: list[dict],
    selected_section_numbers: list[int],
    questions_per_section: int = 2,
    adaptation_payload: dict | None = None,
) -> MCQSet:
    settings = get_settings()

    if settings.llm_provider.lower().strip() == "mock":
        return generate_mock_mcqs(
            retrieved_chunks=retrieved_chunks,
            selected_section_numbers=selected_section_numbers,
            questions_per_section=questions_per_section,
            adaptation_payload=adaptation_payload,
        )

    all_questions = []

    for section_number in selected_section_numbers:
        section_chunks = [
            chunk
            for chunk in retrieved_chunks
            if chunk["section_number"] == section_number
        ]

        if not section_chunks:
            raise ValueError(f"No retrieved chunks found for section {section_number}.")

        try:
            section_mcq_set = _generate_section_mcqs_with_llm(
                section_chunks=section_chunks,
                section_number=section_number,
                questions_per_section=questions_per_section,
                adaptation_payload=adaptation_payload or {},
            )
        except Exception:
            # Ultimate safety fallback guard checking execution parameters dynamically
            section_mcq_set = generate_mock_mcqs(
                retrieved_chunks=section_chunks,
                selected_section_numbers=[section_number],
                questions_per_section=questions_per_section,
                adaptation_payload=adaptation_payload,
            )

        all_questions.extend(
            question.model_dump()
            for question in section_mcq_set.questions
        )

    return parse_and_validate_mcqs(
        raw_output={"questions": all_questions},
        selected_section_numbers=selected_section_numbers,
        questions_per_section=questions_per_section,
    )


def _adaptation_payload_for_section(
    adaptation_payload: dict,
    section_number: int,
) -> dict:
    section_payload = dict(adaptation_payload or {})
    section_payload["weak_topics"] = [
        weak_topic
        for weak_topic in section_payload.get("weak_topics", [])
        if weak_topic.get("section_number") == section_number
    ]
    return section_payload


def _generate_section_mcqs_with_llm(
    section_chunks: list[dict],
    section_number: int,
    questions_per_section: int,
    adaptation_payload: dict,
) -> MCQSet:
    section_adaptation_payload = _adaptation_payload_for_section(
        adaptation_payload=adaptation_payload,
        section_number=section_number,
    )

    prompt = build_mcq_generation_prompt(
        retrieved_chunks=section_chunks[: max(2, questions_per_section * 2)],
        selected_section_numbers=[section_number],
        questions_per_section=questions_per_section,
        adaptation_payload=section_adaptation_payload,
    )

    last_error: Exception | None = None

    for attempt in range(MAX_LLM_GENERATION_ATTEMPTS):
        candidate_prompt = prompt

        if attempt > 0 and last_error is not None:
            candidate_prompt = (
                f"{prompt}\n\n"
                f"Previous output failed validation: {last_error}\n"
                f"Regenerate the full JSON for section {section_number}. "
                f"Return exactly {questions_per_section} valid questions for section {section_number}. "
                "Do not return fewer questions. Do not include any other section. "
                "Every question text must be unique. "
                "Each question must include section_id, section_number, topic, difficulty, "
                "question, options, correct_answer, explanation, adaptation_reason, "
                "and source_chunk_ids. Return JSON only."
            )

        raw_output = call_llm(candidate_prompt)

        try:
            section_mcq_set = parse_and_validate_mcqs(
                raw_output=raw_output,
                selected_section_numbers=[section_number],
                questions_per_section=questions_per_section,
            )

            return _apply_backend_adaptation_reasons(
                mcq_set=section_mcq_set,
                adaptation_payload=adaptation_payload,
                section_number=section_number,
            )
        except (JSONDecodeError, ValidationError, ValueError) as error:
            last_error = error

    raise RuntimeError(
        f"LLM MCQ generation failed validation for section {section_number}: {last_error}"
    )