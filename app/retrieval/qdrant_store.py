from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams, ScoredPoint

from app.core.config import get_settings
from app.retrieval.embeddings import embedding_dimension


def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )


def ensure_collection() -> None:
    settings = get_settings()
    client = get_qdrant_client()

    existing_collections = client.get_collections().collections
    existing_names = {collection.name for collection in existing_collections}

    if settings.qdrant_collection in existing_names:
        return

    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=embedding_dimension(),
            distance=Distance.COSINE,
        ),
    )


def upsert_chunk_vectors(points: list[PointStruct]) -> None:
    settings = get_settings()
    client = get_qdrant_client()

    ensure_collection()

    client.upsert(
        collection_name=settings.qdrant_collection,
        points=points,
    )



# NEW: Optimized Threshold-Tuned Vector Search Query

def search_similar_chunks(query_vector: list[float], limit: int = 4) -> list[ScoredPoint]:
    """
    Queries Qdrant for similar context chunks, strictly filtering out noisy or
    unrelated results falling below our explicit score threshold.
    """
    settings = get_settings()
    client = get_qdrant_client()
    
    ensure_collection()
    
    results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=limit,
        score_threshold=settings.qdrant_score_threshold  # <-- Dynamic threshold wall
    )
    
    return results