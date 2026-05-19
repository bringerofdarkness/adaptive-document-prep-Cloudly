import typer
from qdrant_client.models import PointStruct

from app.db.models import Chunk
from app.db.repositories.document_repo import get_latest_document
from app.db.session import SessionLocal
from app.retrieval.embeddings import embed_texts
from app.retrieval.qdrant_store import ensure_collection, upsert_chunk_vectors


app = typer.Typer(help="Index PostgreSQL chunks into Qdrant.")


def build_point(chunk: Chunk, vector: list[float]) -> PointStruct:
    return PointStruct(
        id=chunk.id,
        vector=vector,
        payload={
            "document_id": chunk.document_id,
            "section_id": chunk.section_id,
            "section_number": chunk.section_number,
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "page_number": chunk.page_number,
            "text_preview": chunk.text_preview,
        },
    )


@app.command()
def index_latest() -> None:
    db = SessionLocal()

    try:
        document = get_latest_document(db)

        if document is None:
            raise typer.BadParameter("No document found. Run PDF ingestion first.")

        chunks = (
            db.query(Chunk)
            .filter(Chunk.document_id == document.id)
            .order_by(Chunk.section_number.asc(), Chunk.chunk_index.asc())
            .all()
        )

        if not chunks:
            raise typer.BadParameter("No chunks found for latest document.")

        typer.echo(f"Latest document_id: {document.id}")
        typer.echo(f"Chunks to index: {len(chunks)}")

        ensure_collection()

        texts = [chunk.text for chunk in chunks]
        vectors = embed_texts(texts)

        points = [
            build_point(chunk=chunk, vector=vector)
            for chunk, vector in zip(chunks, vectors)
        ]

        upsert_chunk_vectors(points)

        for chunk in chunks:
            chunk.qdrant_point_id = chunk.id

        db.commit()

        typer.echo("Qdrant indexing complete.")

    finally:
        db.close()


if __name__ == "__main__":
    app()