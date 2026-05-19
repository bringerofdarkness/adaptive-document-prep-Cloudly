from app.schemas.question import MCQSet
from app.services.scoring_service import score_mcq_answers


def test_scoring_service_scores_correct_and_wrong_answers() -> None:
    mcq_set = MCQSet.model_validate(
        {
            "questions": [
                {
                    "question_id": "q1",
                    "section_id": "section-5",
                    "section_number": 5,
                    "topic": "Topic A",
                    "difficulty": "medium",
                    "question": "Question 1?",
                    "options": {
                        "A": "Correct",
                        "B": "Wrong",
                        "C": "Wrong",
                        "D": "Wrong",
                    },
                    "correct_answer": "A",
                    "explanation": "A is correct.",
                    "adaptation_reason": "Cold-start.",
                    "source_chunk_ids": ["chunk-1"],
                },
                {
                    "question_id": "q2",
                    "section_id": "section-8",
                    "section_number": 8,
                    "topic": "Topic B",
                    "difficulty": "medium",
                    "question": "Question 2?",
                    "options": {
                        "A": "Wrong",
                        "B": "Correct",
                        "C": "Wrong",
                        "D": "Wrong",
                    },
                    "correct_answer": "B",
                    "explanation": "B is correct.",
                    "adaptation_reason": "Adaptive.",
                    "source_chunk_ids": ["chunk-2"],
                },
            ]
        }
    )

    result = score_mcq_answers(
        mcq_set=mcq_set,
        answer_map={
            "q1": "A",
            "q2": "A",
        },
    )

    assert result["total_questions"] == 2
    assert result["correct_count"] == 1
    assert result["wrong_count"] == 1
    assert result["score"] == 50.0
    assert result["results"][1]["clarification"] == "B is correct."