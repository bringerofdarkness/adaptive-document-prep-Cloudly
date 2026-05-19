def chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 180,
) -> list[str]:
    """
    Simple deterministic character chunker.

    Good enough for the take-home because section filtering is more important
    than fancy chunking at this stage.
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
