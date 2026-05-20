import json
from typing import Any
from uuid import uuid4

from ftfy import fix_text

from app.schemas.question import MCQSet


VALID_OPTION_KEYS = {"A", "B", "C", "D"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}


def clean_text_value(value: Any, default: str = "") -> str:
    """
    Normalize user-facing LLM text.

    Uses ftfy to repair common Unicode/mojibake issues without hardcoded
    character replacements. If the text is already valid, it remains unchanged.
    """
    text = str(value if value is not None else default).strip()

    if not text:
        return default

    return fix_text(text).strip()


def _repair_mojibake(text: str) -> str:

    """
    Fix common encoding corruption in LLM/user-facing text.

    Example:
    "Cuartel ValparaÃ­so" becomes "Cuartel Valparaíso".

    This is not a word-specific replacement. It reverses a general UTF-8
    decoding mistake and returns the original text if repair is not possible.
    """

    repaired_text = text

    for _ in range(3):
        if not _looks_like_mojibake(repaired_text):
            break

        repaired_once = repaired_text

        for source_encoding in ("latin1", "cp1252"):
            try:
                candidate = repaired_text.encode(source_encoding).decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue

            if candidate and candidate != repaired_text:
                repaired_once = candidate
                break

        if repaired_once == repaired_text:
            break

        repaired_text = repaired_once

    return repaired_text


def _looks_like_mojibake(text: str) -> bool:
    return any(marker in text for marker in ("Ã", "Â", "â€", "â€™", "â€œ", "â€"))


def _normalize_options(raw_options: Any) -> dict[str, str] | None:
    if isinstance(raw_options, dict):
        options = {
            str(key).strip().upper(): clean_text_value(value)
            for key, value in raw_options.items()
        }

        if set(options.keys()) == VALID_OPTION_KEYS and all(options.values()):
            return options

    if isinstance(raw_options, list) and len(raw_options) == 4:
        return {
            "A": clean_text_value(raw_options[0]),
            "B": clean_text_value(raw_options[1]),
            "C": clean_text_value(raw_options[2]),
            "D": clean_text_value(raw_options[3]),
        }

    return None


def normalize_mcq_payload(payload: dict) -> dict:
    questions = payload.get("questions", [])

    if not isinstance(questions, list):
        return {"questions": []}

    normalized_questions = []
    seen_question_texts = set()

    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            continue

        options = _normalize_options(question.get("options"))

        if options is None:
            continue

        question_text = clean_text_value(
            question.get("question")
            or question.get("question_text")
            or f"Generated MCQ {index}"
        )

        normalized_question_text = question_text.lower()

        if normalized_question_text in seen_question_texts:
            question_text = f"{question_text} ({index})"
            normalized_question_text = question_text.lower()

        seen_question_texts.add(normalized_question_text)

        correct_answer = clean_text_value(
            question.get("correct_answer"),
            "A",
        ).upper()

        if correct_answer not in VALID_OPTION_KEYS:
            correct_answer = "A"

        difficulty = clean_text_value(
            question.get("difficulty"),
            "medium",
        ).lower()

        if difficulty not in VALID_DIFFICULTIES:
            difficulty = "medium"

        try:
            section_number = int(question.get("section_number"))
        except (TypeError, ValueError):
            continue

        normalized_questions.append(
            {
                "question_id": str(uuid4()),
                "section_id": clean_text_value(question.get("section_id")),
                "section_number": section_number,
                "topic": clean_text_value(
                    question.get("topic"),
                    "General section concept",
                ),
                "difficulty": difficulty,
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": clean_text_value(
                    question.get("explanation"),
                    "The answer is grounded in the retrieved source context.",
                ),
                "adaptation_reason": clean_text_value(
                    question.get("adaptation_reason"),
                    "Generated from the selected section and current preparation history.",
                ),
                "source_chunk_ids": question.get("source_chunk_ids") or [],
            }
        )

    return {"questions": normalized_questions}


def enforce_question_distribution(
    payload: dict,
    selected_section_numbers: list[int],
    questions_per_section: int,
) -> dict:
    questions = payload.get("questions", [])
    final_questions = []

    for section_number in selected_section_numbers:
        section_questions = [
            question
            for question in questions
            if question["section_number"] == section_number
        ]

        if len(section_questions) < questions_per_section:
            raise ValueError(
                "Invalid question distribution: "
                f"section {section_number} has {len(section_questions)} questions, "
                f"expected {questions_per_section}."
            )

        final_questions.extend(section_questions[:questions_per_section])

    return {"questions": final_questions}


def parse_and_validate_mcqs(
    raw_output: str | dict[str, Any],
    selected_section_numbers: list[int],
    questions_per_section: int | None = None,
) -> MCQSet:
    if isinstance(raw_output, str):
        payload = normalize_mcq_payload(json.loads(raw_output))
    else:
        payload = raw_output

    invalid_sections = [
        question["section_number"]
        for question in payload.get("questions", [])
        if question["section_number"] not in selected_section_numbers
    ]

    if invalid_sections:
        raise ValueError(
            f"Out-of-selected-section questions detected: {sorted(set(invalid_sections))}"
        )

    if questions_per_section is not None:
        payload = enforce_question_distribution(
            payload=payload,
            selected_section_numbers=selected_section_numbers,
            questions_per_section=questions_per_section,
        )

    return MCQSet.model_validate(payload)