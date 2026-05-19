import json
from typing import Any

from app.schemas.question import MCQSet


def parse_and_validate_mcqs(
    raw_output: str | dict[str, Any],
    selected_section_numbers: list[int],
) -> MCQSet:
    if isinstance(raw_output, str):
        payload = json.loads(raw_output)
    else:
        payload = raw_output

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

    return mcq_set