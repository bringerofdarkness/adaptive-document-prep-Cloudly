from json import JSONDecodeError
from uuid import uuid4

from pydantic import ValidationError

from app.core.config import get_settings
from app.llm.output_parser import parse_and_validate_mcqs
from app.llm.prompts import build_mcq_generation_prompt
from app.llm.providers import call_llm
from app.schemas.question import MCQSet


def _clean_text(text: str, max_length: int = 220) -> str:
    cleaned = " ".join(text.split())

    if len(cleaned) <= max_length:
        return cleaned

    return cleaned[:max_length].rsplit(" ", 1)[0] + "..."


def _topic_from_chunk(section_number: int, chunk_index: int) -> str:
    return f"Section {section_number} concept {chunk_index}"


def generate_mock_mcqs(
    retrieved_chunks: list[dict],
    selected_section_numbers: list[int],
    questions_per_section: int = 2,
    adaptation_payload: dict | None = None,
) -> MCQSet:
    if not retrieved_chunks:
        raise ValueError("Cannot generate MCQs without retrieved chunks.")

    adaptation_payload = adaptation_payload or {}
    weak_topics = adaptation_payload.get("weak_topics", [])

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

            is_adaptive = any(
                weak_topic.get("section_number") == section_number
                for weak_topic in weak_topics
            )

            adaptation_reason = (
                f"Adaptive question because previous history shows weakness in section {section_number}."
                if is_adaptive
                else f"Cold-start coverage question for selected section {section_number}."
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

        section_mcq_set = _generate_section_mcqs_with_llm(
            section_chunks=section_chunks,
            section_number=section_number,
            questions_per_section=questions_per_section,
            adaptation_payload=adaptation_payload or {},
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


def _generate_section_mcqs_with_llm(
    section_chunks: list[dict],
    section_number: int,
    questions_per_section: int,
    adaptation_payload: dict,
) -> MCQSet:
    prompt = build_mcq_generation_prompt(
        retrieved_chunks=section_chunks[: max(2, questions_per_section * 2)],
        selected_section_numbers=[section_number],
        questions_per_section=questions_per_section,
        adaptation_payload=adaptation_payload,
    )

    last_error: Exception | None = None

    for attempt in range(2):
        candidate_prompt = prompt

        if attempt == 1 and last_error is not None:
            candidate_prompt = (
                f"{prompt}\n\n"
                f"Previous output failed validation: {last_error}\n"
                "Regenerate the full JSON. Return exactly the requested number of questions. "
                "Every question text must be unique. Include correct_answer, explanation, "
                "adaptation_reason, section_id, section_number, and source_chunk_ids."
            )

        raw_output = call_llm(candidate_prompt)

        try:
            return parse_and_validate_mcqs(
                raw_output=raw_output,
                selected_section_numbers=[section_number],
                questions_per_section=questions_per_section,
            )
        except (JSONDecodeError, ValidationError, ValueError) as error:
            last_error = error

    raise RuntimeError(
        f"LLM MCQ generation failed validation for section {section_number}: {last_error}"
    )