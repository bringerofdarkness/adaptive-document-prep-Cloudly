from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_prep_start_returns_queued_status_and_task_id(monkeypatch) -> None:
    # Create a mock task object that mimics Celery's dynamic return behavior
    class FakeTask:
        id = "mock-task-id-12345"

    def fake_send_task(name, kwargs=None):
        return FakeTask()

    # Monkeypatch the celery_app instance used inside your API routes layer
    from app.api.routes_prep import celery_app
    monkeypatch.setattr(celery_app, "send_task", fake_send_task)

    # Issue an asynchronous launch post request to the API
    response = client.post(
        "/prep/start",
        json={
            "selected_section_numbers": [5],
            "questions_per_section": 1,
        },
    )

    # Validate your asynchronous contract constraints
    assert response.status_code == 202
    payload = response.json()
    assert payload["task_id"] == "mock-task-id-12345"
    assert payload["status"] == "QUEUED"
    assert "message" in payload


def test_prep_submit_returns_score_and_clarification(monkeypatch) -> None:
    def fake_submit_interactive_prep_answers(db, session_id, answers) -> dict:
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