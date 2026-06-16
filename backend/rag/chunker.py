import re
from typing import List


def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split a document into overlapping chunks.

    Args:
        text: The raw document text.
        chunk_size: Approximate number of characters per chunk.
        overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        A list of text chunks.
    """
    # Clean up whitespace
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = start + chunk_size
        chunk = cleaned[start:end]
        chunks.append(chunk)
        # Move start forward by chunk_size - overlap to create overlapping windows
        start += max(chunk_size - overlap, 1)
    return chunks
