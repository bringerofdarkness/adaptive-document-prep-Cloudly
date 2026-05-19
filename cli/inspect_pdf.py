from pathlib import Path

from app.ingestion.chunker import chunk_text
from app.ingestion.pdf_loader import load_pdf_pages
from app.ingestion.section_parser import extract_sections_from_pages


PDF_PATH = Path("data/SLATEFALL_DOSSIER.pdf")


def main() -> None:
    pages = load_pdf_pages(PDF_PATH)
    sections = extract_sections_from_pages(pages)

    print(f"Loaded pages: {len(pages)}")
    print(f"Extracted sections: {len(sections)}")
    print()

    for section in sections:
        chunks = chunk_text(section["text"])
        print(
            f"Section {section['section_number']}: "
            f"{section['title']} | "
            f"pages {section['start_page']}-{section['end_page']} | "
            f"chunks={len(chunks)}"
        )


if __name__ == "__main__":
    main()
