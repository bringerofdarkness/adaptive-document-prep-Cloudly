def chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 180,
) -> list[str]:
    """
    Simple text chunker.

    Section filtering is the main focus here.
    """
    cleaned = " ".join(text.split())

    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(cleaned):
            break

        start = max(0, end - overlap)

    return chunks
