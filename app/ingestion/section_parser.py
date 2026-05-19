import re


SECTION_PATTERN = re.compile(
    r"Section\s+(\d+)\.\s+(.+?)(?=\n|\r)",
    re.IGNORECASE,
)

PAGE_MARKER_PATTERN = re.compile(r"\[\[PAGE:(\d+)\]\]")


def _page_number_for_position(page_markers: list[tuple[int, int]], position: int) -> int | None:
    """
    Return the page number active at a character position in the combined PDF text.
    """
    active_page = None

    for marker_position, page_number in page_markers:
        if marker_position <= position:
            active_page = page_number
        else:
            break

    return active_page


def extract_sections_from_pages(pages: list[dict]) -> list[dict]:
    """
    Extract real Section 1..10 blocks from the SLATEFALL dossier.

    Returns section_number, title, start_page, end_page, and section text.
    """
    full_text_parts: list[str] = []

    for page in pages:
        marker = f"\n\n[[PAGE:{page['page_number']}]]\n"
        full_text_parts.append(marker + page["text"])

    full_text = "\n".join(full_text_parts)

    page_markers = [
        (match.start(), int(match.group(1)))
        for match in PAGE_MARKER_PATTERN.finditer(full_text)
    ]

    matches = list(SECTION_PATTERN.finditer(full_text))

    # Skip Table of Contents matches by keeping the later real section headings.
    seen_positions_by_number: dict[int, list[re.Match]] = {}

    for match in matches:
        section_number = int(match.group(1))
        if 1 <= section_number <= 10:
            seen_positions_by_number.setdefault(section_number, []).append(match)

    real_matches = []

    for section_number in range(1, 11):
        candidates = seen_positions_by_number.get(section_number, [])
        if not candidates:
            raise ValueError(f"Could not find Section {section_number} in PDF text.")

        # Real section headings appear later than the Table of Contents.
        # Keep the last heading for each section number.
        real_matches.append(candidates[-1])

    real_matches.sort(key=lambda m: m.start())

    sections: list[dict] = []

    for index, match in enumerate(real_matches):
        section_number = int(match.group(1))
        title = " ".join(match.group(2).strip().split())

        start = match.start()
        end = real_matches[index + 1].start() if index + 1 < len(real_matches) else len(full_text)

        start_page = _page_number_for_position(page_markers, start)
        end_page = _page_number_for_position(page_markers, max(start, end - 1))

        section_block = full_text[start:end].strip()
        clean_text = PAGE_MARKER_PATTERN.sub("", section_block).strip()

        sections.append(
            {
                "section_number": section_number,
                "title": title,
                "start_page": start_page,
                "end_page": end_page,
                "text": clean_text,
            }
        )

    return sections
