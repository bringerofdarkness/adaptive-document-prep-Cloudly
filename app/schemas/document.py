from pydantic import BaseModel


class SectionResponse(BaseModel):
    section_id: str
    section_number: int
    title: str
    start_page: int
    end_page: int
    chunk_count: int


class DocumentSectionsResponse(BaseModel):
    document_id: str
    filename: str
    title: str | None
    total_pages: int
    sections: list[SectionResponse]