from sqlalchemy.orm import Session
from qdrant_client.models import FieldCondition, Filter, MatchValue

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
    
    if not selected_section_numbers:
        raise ValueError("At least one section number must be selected.")

    settings = get_settings()
    client = get_qdrant_client()
    query_vector = embed_texts([query])[0]  

    per_section_limit = max(1, limit // len(selected_section_numbers))
    points = []

    for section_number in selected_section_numbers:
        qdrant_filter = Filter(
            must=[
                FieldCondition(
                    key="section_number",
                    match=MatchValue(value=int(section_number)),
                ),
            ]
        )

        response = client.query_points(
            collection_name=settings.qdrant_collection,     #Settings=config
            query=query_vector,
            query_filter=qdrant_filter,
            limit=per_section_limit,
            with_payload=True,
        )

        points.extend(response.points)  #added results to point list

    points = sorted(points, key=lambda point: point.score or 0.0, reverse=True)[:limit]
    chunk_ids = list(dict.fromkeys(str(point.payload["chunk_id"]) for point in points))

    if not chunk_ids:
        return []

    chunks = db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()
    chunks_by_id = {str(chunk.id): chunk for chunk in chunks}

    retrieved = []
    for point in points:
        chunk_id = str(point.payload["chunk_id"])
        chunk = chunks_by_id.get(chunk_id)

        if chunk is None:
            continue

        retrieved.append(      #adding chunk info to final list
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