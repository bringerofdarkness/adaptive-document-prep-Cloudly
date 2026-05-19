import json
from typing import Any
from uuid import uuid4
from app.schemas.question import MCQSet


VALID_OPTION_KEYS = {"A", "B", "C", "D"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}


def _clean_text_value(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()

    if not text:
        return default

    if any(marker in text for marker in ("Ã", "Â", "â")):
        try:
            return text.encode("latin1").decode("utf-8").strip()
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text

    return text


def _normalize_options(raw_options: Any) -> dict[str, str] | None:
    if isinstance(raw_options, dict):
        options = {
            str(key).strip().upper(): _clean_text_value(value)
            for key, value in raw_options.items()
        }

        if set(options.keys()) == VALID_OPTION_KEYS and all(options.values()):
            return options

    if isinstance(raw_options, list) and len(raw_options) == 4:
        return {
            "A": _clean_text_value(raw_options[0]),
            "B": _clean_text_value(raw_options[1]),
            "C": _clean_text_value(raw_options[2]),
            "D": _clean_text_value(raw_options[3]),
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

        question_text = _clean_text_value(
            question.get("question")
            or question.get("question_text")
            or f"Generated MCQ {index}"
        )

        normalized_question_text = question_text.lower()

        if normalized_question_text in seen_question_texts:
            question_text = f"{question_text} ({index})"
            normalized_question_text = question_text.lower()

        seen_question_texts.add(normalized_question_text)

        correct_answer = str(question.get("correct_answer") or "A").strip().upper()

        if correct_answer not in VALID_OPTION_KEYS:
            correct_answer = "A"

        difficulty = str(question.get("difficulty") or "medium").strip().lower()

        if difficulty not in VALID_DIFFICULTIES:
            difficulty = "medium"

        normalized_questions.append(
            {
                "question_id": str(uuid4()),
                "section_id": str(question.get("section_id") or ""),
                "section_number": int(question.get("section_number")),
                "topic": _clean_text_value(question.get("topic"), "General section concept"),
                "difficulty": difficulty,
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "explanation": _clean_text_value(
                    question.get("explanation"),
                    "The answer is grounded in the retrieved source context.",
                ),
                "adaptation_reason": _clean_text_value(
                    question.get("adaptation_reason"),
                    "Generated from the selected section and current preparation history.",
                ),
                "source_chunk_ids": question.get("source_chunk_ids") or [],
            }
        )

    return {"questions": normalized_questions}


def parse_and_validate_mcqs(
    raw_output: str | dict[str, Any],
    selected_section_numbers: list[int],
    questions_per_section: int | None = None,
) -> MCQSet:
    if isinstance(raw_output, str):
        payload = json.loads(raw_output)
    else:
        payload = raw_output

    payload = normalize_mcq_payload(payload)
    mcq_set = MCQSet.model_validate(payload)

    invalid_sections = [
        question.section_number
        for question in mcq_set.questions
        if question.section_number not in selected_section_numbers
    ]

    if invalid_sections:
        raise ValueError(
            f"Out-of-selected-section questions detected: {sorted(set(invalid_sections))}"
        )

    if questions_per_section is not None:
        for section_number in selected_section_numbers:
            section_question_count = sum(
                1
                for question in mcq_set.questions
                if question.section_number == section_number
            )

            if section_question_count != questions_per_section:
                raise ValueError(
                    "Invalid question distribution: "
                    f"section {section_number} has {section_question_count} questions, "
                    f"expected {questions_per_section}."
                )

    return mcq_set