from pathlib import Path

import fitz


def load_pdf_pages(pdf_path: str | Path) -> list[dict]:
    """Load machine-readable PDF pages using PyMuPDF."""
    path = Path(pdf_path)

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

    return pages
