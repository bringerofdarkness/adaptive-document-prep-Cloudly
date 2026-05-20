import json

MAX_CONTEXT_CHUNKS = 4
MAX_CHARS_PER_CHUNK = 350
MAX_WEAK_TOPICS = 3
MAX_HISTORY_ITEMS = 2


def _compact_text(text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> str:
    cleaned = " ".join(text.split())

    if len(cleaned) <= max_chars:
        return cleaned

    return cleaned[:max_chars].rsplit(" ", 1)[0] + "..."


def _compact_adaptation_payload(adaptation_payload: dict) -> dict:
    return {
        "is_returning_run": adaptation_payload.get("is_returning_run", False),
        "mode": adaptation_payload.get("mode", "cold_start"),
        "relevant_prior_session_count": adaptation_payload.get(
            "relevant_prior_session_count",
            0,
        ),
        "summary": adaptation_payload.get("summary"),
        "weak_topics": adaptation_payload.get("weak_topics", [])[:MAX_WEAK_TOPICS],
        "mastered_question_texts": adaptation_payload.get(
            "mastered_question_texts",
            [],
        )[:MAX_HISTORY_ITEMS],
        "previous_wrong_question_texts": adaptation_payload.get(
            "previous_wrong_question_texts",
            [],
        )[:MAX_HISTORY_ITEMS],
    }

def _adaptation_reason_guidance(compact_adaptation_payload: dict) -> str:
    mode = compact_adaptation_payload.get("mode", "cold_start")
    weak_topics = compact_adaptation_payload.get("weak_topics", [])

    if mode == "adaptive" and weak_topics:
        return (
            "For adaptation_reason, explain that the question targets prior weak "
            "topics or mistakes from previous sessions."
        )

    if mode == "adaptive":
        return (
            "For adaptation_reason, explain that the question is part of a returning "
            "run using previous session history, without claiming a weak topic unless "
            "one is provided."
        )

    return (
        "For adaptation_reason, explain that this is cold-start section coverage "
        "because no prior relevant learning history exists."
    )


def build_mcq_generation_prompt(
    retrieved_chunks: list[dict],
    selected_section_numbers: list[int],
    questions_per_section: int,
    adaptation_payload: dict,
) -> str:
    context_blocks = []

    for chunk in retrieved_chunks[:MAX_CONTEXT_CHUNKS]:
        context_blocks.append(
            {
                "chunk_id": chunk["chunk_id"],
                "section_id": chunk["section_id"],
                "section_number": chunk["section_number"],
                "chunk_index": chunk["chunk_index"],
                "text": _compact_text(chunk["text"]),
            }
        )

    compact_adaptation_payload = _compact_adaptation_payload(adaptation_payload)
    adaptation_reason_guidance = _adaptation_reason_guidance(compact_adaptation_payload)

    return f"""
You are generating assessment-quality MCQs from a selected PDF corpus.

Selected section numbers:
{selected_section_numbers}

Questions per selected section:
{questions_per_section}

Adaptive context:
{json.dumps(compact_adaptation_payload, indent=2)}

Retrieved source chunks:
{json.dumps(context_blocks, indent=2)}

Rules:
- Use only selected sections and provided chunks.
- Return JSON only, no markdown.
- Generate exactly {questions_per_section} questions per selected section.
- Each MCQ must have A, B, C, D, one correct answer, concise explanation, and adaptation_reason.
- If weak_topics exist, prioritize them. Avoid close repeats of mastered questions.
- Every question text must be unique.
- Each question must test a different specific fact, concept, or relationship from the provided chunks.
- Keep question, options, explanation, and adaptation_reason concise.

JSON shape:
{{"questions":[{{"question_id":"unique-string","section_id":"source section id","section_number":5,"topic":"short topic","difficulty":"easy|medium|hard","question":"text","options":{{"A":"text","B":"text","C":"text","D":"text"}},"correct_answer":"A","explanation":"text","adaptation_reason":"text","source_chunk_ids":["chunk id"]}}]}}
""".strip()