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


AnswerKey = Literal["A", "B", "C", "D"]


class PrepStartRequest(BaseModel):
    selected_section_numbers: list[int] = Field(min_length=1)
    questions_per_section: int = Field(default=2, ge=1, le=5)


class PrepQuestionForUser(BaseModel):
    question_id: str
    section_number: int
    topic: str
    difficulty: str
    question: str
    options: dict[str, str]
    adaptation_reason: str


class PrepStartResponse(BaseModel):
    session_id: str
    document_id: str
    mode: str
    selected_sections: list[int]
    total_questions: int
    adaptation_summary: str | None = None
    questions: list[PrepQuestionForUser]


class PrepSubmitRequest(BaseModel):
    session_id: str
    answers: dict[str, AnswerKey]


class PrepQuestionResult(BaseModel):
    question_id: str
    section_number: int
    topic: str
    selected_answer: AnswerKey
    correct_answer: AnswerKey
    is_correct: bool
    clarification: str | None = None


class PrepSubmitResponse(BaseModel):
    session_id: str
    score: float
    total_questions: int
    correct_count: int
    wrong_count: int
    results: list[PrepQuestionResult]