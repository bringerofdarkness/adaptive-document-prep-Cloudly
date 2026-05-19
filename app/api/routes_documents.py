from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document, Section
from app.db.session import get_db
from app.schemas.document import DocumentSectionsResponse, SectionResponse


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}/sections", response_model=DocumentSectionsResponse)
def get_document_sections(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentSectionsResponse:
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    sections = (
        db.query(Section)
        .filter(Section.document_id == document_id)
        .order_by(Section.section_number.asc())
        .all()
    )

    section_responses = []

    for section in sections:
        chunk_count = (
            db.query(Chunk)
            .filter(Chunk.section_id == section.id)
            .count()
        )

        section_responses.append(
            SectionResponse(
                section_id=section.id,
                section_number=section.section_number,
                title=section.title,
                start_page=section.start_page,
                end_page=section.end_page,
                chunk_count=chunk_count,
            )
        )

    return DocumentSectionsResponse(
        document_id=document.id,
        filename=document.filename,
        title=document.title,
        total_pages=document.total_pages,
        sections=section_responses,
    )