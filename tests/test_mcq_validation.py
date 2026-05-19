import pytest

from app.llm.output_parser import parse_and_validate_mcqs


def valid_payload() -> dict:
    return {
        "questions": [
            {
                "question_id": "q1",
                "section_id": "section-5",
                "section_number": 5,
                "topic": "Doctrine",
                "difficulty": "medium",
                "question": "Which option is grounded in the selected section?",
                "options": {
                    "A": "Correct grounded option",
                    "B": "Wrong option",
                    "C": "Wrong option",
                    "D": "Wrong option",
                },
                "correct_answer": "A",
                "explanation": "The answer is grounded in the selected section.",
                "adaptation_reason": "Cold-start coverage question.",
                "source_chunk_ids": ["chunk-1"],
            }
        ]
    }


def test_valid_mcq_payload_passes_validation() -> None:
    mcq_set = parse_and_validate_mcqs(
        raw_output=valid_payload(),
        selected_section_numbers=[5],
        questions_per_section=1,
    )

    assert len(mcq_set.questions) == 1
    assert mcq_set.questions[0].section_number == 5
    assert mcq_set.questions[0].correct_answer == "A"


def test_out_of_selected_section_question_fails_validation() -> None:
    payload = valid_payload()
    payload["questions"][0]["section_number"] = 8

    with pytest.raises(ValueError, match="Out-of-selected-section"):
        parse_and_validate_mcqs(
            raw_output=payload,
            selected_section_numbers=[5],
            questions_per_section=1,
        )


def test_invalid_question_distribution_fails_validation() -> None:
    with pytest.raises(ValueError, match="Invalid question distribution"):
        parse_and_validate_mcqs(
            raw_output=valid_payload(),
            selected_section_numbers=[5],
            questions_per_section=2,
        )