from sqlalchemy.orm import Session

from app.db.models import Chunk, Document, Section


def create_document_with_sections_and_chunks(
    db: Session,
    filename: str,
    title: str,
    source_path: str,
    total_pages: int,
    sections_payload: list[dict],
) -> Document:
    document = Document(
        filename=filename,
        title=title,
        source_path=source_path,
        total_pages=total_pages,
    )

    db.add(document)
    db.flush()

    for section_payload in sections_payload:
        section = Section(
            document_id=document.id,
            section_number=section_payload["section_number"],
            title=section_payload["title"],
            start_page=section_payload["start_page"],
            end_page=section_payload["end_page"],
            text=section_payload["text"],
        )

        db.add(section)
        db.flush()

        for chunk_index, chunk_text in enumerate(section_payload["chunks"], start=1):
            chunk = Chunk(
                document_id=document.id,
                section_id=section.id,
                section_number=section.section_number,
                chunk_index=chunk_index,
                page_number=section.start_page,
                text=chunk_text,
                text_preview=chunk_text[:300],
            )
            db.add(chunk)

    db.commit()
    db.refresh(document)

    return document


def get_latest_document(db: Session) -> Document | None:
    return db.query(Document).order_by(Document.created_at.desc()).first()