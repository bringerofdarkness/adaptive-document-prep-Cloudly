import json
import time
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


def _apply_backend_adaptation_reasons_to_all(
    mcq_set: MCQSet,
    adaptation_payload: dict,
) -> MCQSet:
    questions = []
    for question in mcq_set.questions:
        question_payload = question.model_dump()
        question_payload["adaptation_reason"] = _adaptation_reason_from_payload(
            adaptation_payload=adaptation_payload,
            section_number=question_payload["section_number"],
        )
        questions.append(question_payload)

    return MCQSet.model_validate({"questions": questions})


def get_mock_provider_response(prompt: str) -> str:
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
            continue

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

    if not retrieved_chunks:
        raise ValueError("Cannot generate MCQs without retrieved chunks.")

    # Split processing into safe, medium-sized chunks of 2 sections per trip
    segment_size = 2
    compiled_questions = []
    
    for i in range(0, len(selected_section_numbers), segment_size):
        target_sections = selected_section_numbers[i : i + segment_size]
        
        # Filter chunks relevant only to the active micro-batch
        target_chunks = [
            c for c in retrieved_chunks if c["section_number"] in target_sections
        ]
        
        if not target_chunks:
            continue

        try:
            segment_set = _generate_all_mcqs_in_batch(
                retrieved_chunks=target_chunks,
                selected_section_numbers=target_sections,
                questions_per_section=questions_per_section,
                adaptation_payload=adaptation_payload or {},
            )
            compiled_questions.extend(
                q.model_dump() for q in segment_set.questions
            )
            
            # Small protective rest window between API requests to satisfy token limits
            if i + segment_size < len(selected_section_numbers):
                time.sleep(2.0)
                
        except Exception:
            # Fallback to local mock data generation specifically for the failed segment
            fallback_set = generate_mock_mcqs(
                retrieved_chunks=target_chunks,
                selected_section_numbers=target_sections,
                questions_per_section=questions_per_section,
                adaptation_payload=adaptation_payload,
            )
            compiled_questions.extend(
                q.model_dump() for q in fallback_set.questions
            )

    return parse_and_validate_mcqs(
        raw_output={"questions": compiled_questions},
        selected_section_numbers=selected_section_numbers,
        questions_per_section=questions_per_section,
    )


def _generate_all_mcqs_in_batch(
    retrieved_chunks: list[dict],
    selected_section_numbers: list[int],
    questions_per_section: int,
    adaptation_payload: dict,
) -> MCQSet:
    prompt = build_mcq_generation_prompt(
        retrieved_chunks=retrieved_chunks,
        selected_section_numbers=selected_section_numbers,
        questions_per_section=questions_per_section,
        adaptation_payload=adaptation_payload,
    )

    last_error: Exception | None = None

    for attempt in range(MAX_LLM_GENERATION_ATTEMPTS):
        candidate_prompt = prompt

        if attempt > 0 and last_error is not None:
            candidate_prompt = (
                f"{prompt}\n\n"
                f"Previous output failed validation: {last_error}\n"
                f"Regenerate the complete unified JSON array for all sections: {selected_section_numbers}. "
                f"Return exactly {questions_per_section} valid questions per section. "
                "Every question text must be completely unique. "
                "Return valid JSON only."
            )

        raw_output = call_llm(candidate_prompt)

        try:
            batch_mcq_set = parse_and_validate_mcqs(
                raw_output=raw_output,
                selected_section_numbers=selected_section_numbers,
                questions_per_section=questions_per_section,
            )

            return _apply_backend_adaptation_reasons_to_all(
                mcq_set=batch_mcq_set,
                adaptation_payload=adaptation_payload,
            )
        except (JSONDecodeError, ValidationError, ValueError) as error:
            last_error = error

    raise RuntimeError(
        f"LLM MCQ batch generation failed validation for sections {selected_section_numbers}: {last_error}"
    )