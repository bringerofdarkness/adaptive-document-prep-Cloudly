from app.llm.output_parser import parse_and_validate_mcqs


def main() -> None:
    valid_payload = {
        "questions": [
            {
                "question_id": "q1",
                "section_id": "section-5",
                "section_number": 5,
                "topic": "Test Topic",
                "difficulty": "medium",
                "question": "Which option is correct?",
                "options": {
                    "A": "Wrong option",
                    "B": "Correct option",
                    "C": "Wrong option",
                    "D": "Wrong option",
                },
                "correct_answer": "B",
                "explanation": "B is correct because this is a validation test.",
                "adaptation_reason": "Cold-start question for selected section.",
                "source_chunk_ids": ["chunk-1"],
            }
        ]
    }

    mcq_set = parse_and_validate_mcqs(
        raw_output=valid_payload,
        selected_section_numbers=[5, 8],
    )

    print(f"Validated questions: {len(mcq_set.questions)}")
    print("MCQ validation passed.")


if __name__ == "__main__":
    main()