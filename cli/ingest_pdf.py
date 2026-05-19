from pathlib import Path

import typer

from app.db.repositories.document_repo import create_document_with_sections_and_chunks
from app.db.session import SessionLocal
from app.ingestion.chunker import chunk_text
from app.ingestion.pdf_loader import load_pdf_pages
from app.ingestion.section_parser import extract_sections_from_pages


app = typer.Typer(help="Ingest PDF into PostgreSQL.")


@app.command()
def ingest(
    pdf_path: str = "data/SLATEFALL_DOSSIER.pdf",
) -> None:
    path = Path(pdf_path)

    pages = load_pdf_pages(path)
    sections = extract_sections_from_pages(pages)

    sections_payload = []

    for section in sections:
        chunks = chunk_text(section["text"])
        sections_payload.append(
            {
                **section,
                "chunks": chunks,
            }
        )

    db = SessionLocal()

    try:
        document = create_document_with_sections_and_chunks(
            db=db,
            filename=path.name,
            title="SLATEFALL: PAMC Operational Dossier",
            source_path=str(path),
            total_pages=len(pages),
            sections_payload=sections_payload,
        )

        typer.echo(f"Ingested document_id: {document.id}")
        typer.echo(f"Pages: {len(pages)}")
        typer.echo(f"Sections: {len(sections)}")
        typer.echo(f"Chunks: {sum(len(item['chunks']) for item in sections_payload)}")

    finally:
        db.close()


if __name__ == "__main__":
    app()