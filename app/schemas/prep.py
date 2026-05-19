from typing import Literal

from pydantic import BaseModel, Field


SimulationStrategy = Literal["section8_weak", "alternating", "all_correct"]


class PrepRunRequest(BaseModel):
    selected_section_numbers: list[int] = Field(min_length=1)
    questions_per_section: int = Field(default=2, ge=1, le=5)
    simulation_strategy: SimulationStrategy = "section8_weak"


class PrepRunResponse(BaseModel):
    session_id: str
    document_id: str
    selected_sections: list[int]
    mode: str
    score: float
    total_questions: int
    correct_count: int
    wrong_count: int
    adaptation_summary: str | None = None
    relevant_prior_session_count: int | None = None