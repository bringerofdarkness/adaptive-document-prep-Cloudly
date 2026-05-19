from app.schemas.question import MCQSet


VALID_ANSWERS = {"A", "B", "C", "D"}


def score_mcq_answers(
    mcq_set: MCQSet,
    answer_map: dict[str, str],
) -> dict:
    results = []
    correct_count = 0

    for question in mcq_set.questions:
        selected_answer = answer_map.get(question.question_id)

        if selected_answer not in VALID_ANSWERS:
            raise ValueError(
                f"Invalid or missing answer for question_id={question.question_id}"
            )

        is_correct = selected_answer == question.correct_answer

        if is_correct:
            correct_count += 1

        results.append(
            {
                "question_id": question.question_id,
                "selected_answer": selected_answer,
                "correct_answer": question.correct_answer,
                "is_correct": is_correct,
                "clarification": None if is_correct else question.explanation,
            }
        )

    total_questions = len(mcq_set.questions)
    wrong_count = total_questions - correct_count
    score = round((correct_count / total_questions) * 100, 2) if total_questions else 0.0

    return {
        "total_questions": total_questions,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "score": score,
        "results": results,
    }