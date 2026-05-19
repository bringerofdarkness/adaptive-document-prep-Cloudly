from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


AnswerKey = Literal["A", "B", "C", "D"]
Difficulty = Literal["easy", "medium", "hard"]


class MCQQuestion(BaseModel):
    question_id: str = Field(min_length=1)
    section_id: str = Field(min_length=1)
    section_number: int
    topic: str = Field(min_length=1)
    difficulty: Difficulty
    question: str = Field(min_length=1)
    options: dict[AnswerKey, str]
    correct_answer: AnswerKey
    explanation: str = Field(min_length=1)
    adaptation_reason: str = Field(min_length=1)
    source_chunk_ids: list[str] = Field(default_factory=list)

    @field_validator("options")
    @classmethod
    def validate_options(cls, options: dict[str, str]) -> dict[str, str]:
        expected_keys = {"A", "B", "C", "D"}

        if set(options.keys()) != expected_keys:
            raise ValueError("Options must contain exactly A, B, C, and D.")

        for key, value in options.items():
            if not value or not value.strip():
                raise ValueError(f"Option {key} cannot be empty.")

        return options

    @model_validator(mode="after")
    def validate_correct_answer_exists(self) -> "MCQQuestion":
        if self.correct_answer not in self.options:
            raise ValueError("Correct answer must exist in options.")

        return self


class MCQSet(BaseModel):
    questions: list[MCQQuestion]

    @model_validator(mode="after")
    def validate_no_duplicate_questions(self) -> "MCQSet":
        normalized_questions = [
            question.question.strip().lower()
            for question in self.questions
        ]

        if len(normalized_questions) != len(set(normalized_questions)):
            raise ValueError("Duplicate question text detected.")

        return self