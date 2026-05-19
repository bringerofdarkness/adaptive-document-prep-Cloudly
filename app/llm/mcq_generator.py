from uuid import uuid4

from app.llm.output_parser import parse_and_validate_mcqs
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
    """
    Deterministic local MCQ generator used for development and testing.

    It does not replace the final LLM implementation.
    It gives us valid structured MCQs so we can build persistence,
    scoring, adaptation, APIs, and Scenario B exports first.
    """
    if not retrieved_chunks:
        raise ValueError("Cannot generate MCQs without retrieved chunks.")

    adaptation_payload = adaptation_payload or {}
    weak_topics = adaptation_payload.get("weak_topics", [])

    grouped_chunks: dict[int, list[dict]] = {}

    for chunk in retrieved_chunks:
        section_number = chunk["section_number"]
        grouped_chunks.setdefault(section_number, []).append(chunk)

    questions = []

    for section_number in selected_section_numbers:
        section_chunks = grouped_chunks.get(section_number, [])

        if not section_chunks:
            continue

        for index, chunk in enumerate(section_chunks[:questions_per_section], start=1):
            topic = _topic_from_chunk(section_number, chunk["chunk_index"])
            source_preview = _clean_text(chunk["text"])

            is_adaptive = any(
                weak_topic.get("section_number") == section_number
                for weak_topic in weak_topics
            )

            if is_adaptive:
                adaptation_reason = (
                    f"Adaptive question because previous history shows weakness "
                    f"in section {section_number}."
                )
            else:
                adaptation_reason = (
                    f"Cold-start coverage question for selected section {section_number}."
                )

            questions.append(
                {
                    "question_id": str(uuid4()),
                    "section_id": chunk["section_id"],
                    "section_number": section_number,
                    "topic": topic,
                    "difficulty": "medium",
                    "question": (
                        f"Which option best reflects the selected source material "
                        f"for {topic}?"
                    ),
                    "options": {
                        "A": source_preview,
                        "B": "A statement from an unrelated section.",
                        "C": "A contradictory interpretation of the selected material.",
                        "D": "A generic answer not grounded in the selected section.",
                    },
                    "correct_answer": "A",
                    "explanation": (
                        "Option A is correct because it is directly derived from the "
                        "retrieved chunk for the selected section."
                    ),
                    "adaptation_reason": adaptation_reason,
                    "source_chunk_ids": [chunk["chunk_id"]],
                }
            )

    payload = {"questions": questions}

    return parse_and_validate_mcqs(
        raw_output=payload,
        selected_section_numbers=selected_section_numbers,
    )