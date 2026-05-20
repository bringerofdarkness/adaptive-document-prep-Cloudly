from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_prep_start_hides_correct_answer(monkeypatch) -> None:
    def fake_start_interactive_prep_session(
        db,
        selected_section_numbers,
        questions_per_section,
    ) -> dict:
        return {
            "session_id": "session-1",
            "document_id": "document-1",
            "mode": "cold_start",
            "selected_sections": selected_section_numbers,
            "total_questions": 1,
            "adaptation_summary": "Cold-start run.",
            "questions": [
                {
                    "question_id": "question-1",
                    "section_number": selected_section_numbers[0],
                    "topic": "Doctrine",
                    "difficulty": "medium",
                    "question": "What is the selected-section concept?",
                    "options": {
                        "A": "Correct option",
                        "B": "Wrong option",
                        "C": "Wrong option",
                        "D": "Wrong option",
                    },
                    "adaptation_reason": "Cold-start coverage.",
                }
            ],
        }

    monkeypatch.setattr(
        "app.api.routes_prep.start_interactive_prep_session",
        fake_start_interactive_prep_session,
    )

    response = client.post(
        "/prep/start",
        json={
            "selected_section_numbers": [5],
            "questions_per_section": 1,
        },
    )

    assert response.status_code == 200

    payload = response.json()
    question = payload["questions"][0]

    assert payload["session_id"] == "session-1"
    assert payload["mode"] == "cold_start"
    assert question["options"]["A"] == "Correct option"
    assert "correct_answer" not in question
    assert "explanation" not in question


def test_prep_submit_returns_score_and_clarification(monkeypatch) -> None:
    def fake_submit_interactive_prep_answers(
        db,
        session_id,
        answers,
    ) -> dict:
        return {
            "session_id": session_id,
            "score": 0.0,
            "total_questions": 1,
            "correct_count": 0,
            "wrong_count": 1,
            "results": [
                {
                    "question_id": "question-1",
                    "section_number": 8,
                    "topic": "Safehouses",
                    "selected_answer": answers["question-1"],
                    "correct_answer": "A",
                    "is_correct": False,
                    "clarification": "Option A is grounded in the selected section.",
                }
            ],
        }

    monkeypatch.setattr(
        "app.api.routes_prep.submit_interactive_prep_answers",
        fake_submit_interactive_prep_answers,
    )

    response = client.post(
        "/prep/submit",
        json={
            "session_id": "session-1",
            "answers": {
                "question-1": "B",
            },
        },
    )

    assert response.status_code == 200

    payload = response.json()
    result = payload["results"][0]

    assert payload["score"] == 0.0
    assert payload["wrong_count"] == 1
    assert result["selected_answer"] == "B"
    assert result["correct_answer"] == "A"
    assert result["is_correct"] is False
    assert result["clarification"] == "Option A is grounded in the selected section."