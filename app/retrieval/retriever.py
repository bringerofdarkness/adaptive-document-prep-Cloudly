from sqlalchemy.orm import Session
from qdrant_client.models import FieldCondition, Filter, MatchAny

from app.core.config import get_settings
from app.db.models import Chunk, Document
from app.retrieval.embeddings import embed_texts
from app.retrieval.qdrant_store import get_qdrant_client


def retrieve_chunks_for_sections(
    db: Session,
    document: Document,
    selected_section_numbers: list[int],
    query: str,
    limit: int = 8,
) -> list[dict]:
    """
    Retrieve chunks only from selected sections using strict Qdrant metadata filtering.
    PostgreSQL remains the source of truth for full chunk text.
    """
    if not selected_section_numbers:
        raise ValueError("At least one section number must be selected.")

    settings = get_settings()
    client = get_qdrant_client()

    query_vector = embed_texts([query])[0]

    qdrant_filter = Filter(
        must=[
            FieldCondition(
                key="document_id",
                match=MatchAny(any=[document.id]),
            ),
            FieldCondition(
                key="section_number",
                match=MatchAny(any=selected_section_numbers),
            ),
        ]
    )

    response = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        query_filter=qdrant_filter,
        limit=limit,
        with_payload=True,
    )

    points = response.points
    chunk_ids = [str(point.payload["chunk_id"]) for point in points]

    if not chunk_ids:
        return []

    chunks = (
        db.query(Chunk)
        .filter(Chunk.id.in_(chunk_ids))
        .all()
    )

    chunks_by_id = {chunk.id: chunk for chunk in chunks}

    retrieved = []

    for point in points:
        chunk_id = str(point.payload["chunk_id"])
        chunk = chunks_by_id.get(chunk_id)

        if chunk is None:
            continue

        retrieved.append(
            {
                "chunk_id": chunk.id,
                "section_id": chunk.section_id,
                "section_number": chunk.section_number,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "score": point.score,
                "text": chunk.text,
                "text_preview": chunk.text_preview,
            }
        )

    return retrieved