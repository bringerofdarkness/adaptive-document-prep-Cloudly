import io
from pathlib import Path
import typer

from app.core.config import get_settings
from app.core.minio_client import minio_client
from app.db.repositories.document_repo import create_document_with_sections_and_chunks
from app.db.session import SessionLocal
from app.ingestion.chunker import chunk_text
from app.ingestion.pdf_loader import load_pdf_pages
from app.ingestion.section_parser import extract_sections_from_pages

settings = get_settings()
app = typer.Typer(help="Ingest PDF into MinIO and PostgreSQL.")


@app.command()
def ingest(
    pdf_path: str = "data/SLATEFALL_DOSSIER.pdf",
) -> None:
    local_path = Path(pdf_path)
    if not local_path.exists():
        typer.echo(f"Error: Local file not found at {pdf_path}", err=True)
        raise typer.Exit(code=1)

    object_name = local_path.name
    bucket_name = settings.minio_bucket_name

    # --- Phase 1: Upload Raw Document to MinIO (Bronze Layer) ---
    try:
        typer.echo(f"Verifying Object Storage Asset: '{object_name}' in bucket '{bucket_name}'...")
        try:
            minio_client.stat_object(bucket_name, object_name)
            typer.echo("Document already exists in MinIO. Skipping upload phase.")
        except Exception:
            # Object does not exist, upload it securely
            typer.echo("Uploading raw document to cloud storage tier...")
            minio_client.fput_object(bucket_name, object_name, str(local_path))
            typer.echo("Successfully committed object to Bronze Layer.")
    except Exception as e:
        typer.echo(f"Storage Layer Failure: {str(e)}", err=True)
        raise typer.Exit(code=1)

    # --- Phase 2: Stream Raw Bytes into Data Extraction Pipeline ---
    try:
        typer.echo("Streaming object bytes from MinIO into volatile memory buffer...")
        response = minio_client.get_object(bucket_name, object_name)
        pdf_stream = io.BytesIO(response.read())
    except Exception as e:
        typer.echo(f"Failed to stream asset from MinIO: {str(e)}", err=True)
        raise typer.Exit(code=1)
    finally:
        response.close()
        response.release_conn()

    # Pass the stateless stream directly into the PyMuPDF reader
    pages = load_pdf_pages(pdf_stream)
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

    # --- Phase 3: Persist Metadata Configurations to RDBMS ---
    db = SessionLocal()
    try:
        document = create_document_with_sections_and_chunks(
            db=db,
            filename=object_name,
            title="SLATEFALL: PAMC Operational Dossier",
            source_path=f"minio://{bucket_name}/{object_name}",  # Standardized cloud path reference
            total_pages=len(pages),
            sections_payload=sections_payload,
        )

        typer.echo("\n🚀 Ingestion pipeline execution completed successfully!")
        typer.echo(f"Assigned Document Database ID: {document.id}")
        typer.echo(f"Extracted Pages count: {len(pages)}")
        typer.echo(f"Parsed Section Records: {len(sections)}")
        typer.echo(f"Generated Vector Chunks: {sum(len(item['chunks']) for item in sections_payload)}")

    finally:
        db.close()


if __name__ == "__main__":
    app()