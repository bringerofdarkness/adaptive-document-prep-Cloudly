import io
from pathlib import Path
import fitz


def load_pdf_pages(pdf_source: str | Path | io.BytesIO) -> list[dict]:
    """
    Load machine-readable PDF pages using PyMuPDF.
    Accepts local file paths or in-memory binary streams from object storage.
    """
    if isinstance(pdf_source, io.BytesIO):
        # Open directly from the in-memory byte stream fetched from MinIO
        # PyMuPDF uses 'filetype' to decode binary buffers polymorphically
        doc = fitz.open(stream=pdf_source.read(), filetype="pdf")
    else:
        # Fallback to legacy disk-path processing
        path = Path(pdf_source)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        doc = fitz.open(path)

    pages: list[dict] = []

    for index, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        pages.append(
            {
                "page_number": index,
                "text": text,
            }
        )

    doc.close()
    return pages