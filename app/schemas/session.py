from pydantic import BaseModel


class SessionSummaryResponse(BaseModel):
    session_id: str
    document_id: str
    mode: str
    selected_sections: list[int]
    score: float
    total_questions: int
    correct_count: int
    wrong_count: int
    adaptation_summary: str | None = None
    created_at: str