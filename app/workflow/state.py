from typing import TypedDict

from app.schemas.question import MCQSet


class PrepWorkflowState(TypedDict, total=False):
    db: object
    document: object
    selected_section_numbers: list[int]
    questions_per_section: int
    simulation_strategy: str
    adaptation_payload: dict
    retrieved_chunks: list[dict]
    mcq_set: MCQSet
    answer_map: dict[str, str]
    scoring_payload: dict
    session: object
    result: dict