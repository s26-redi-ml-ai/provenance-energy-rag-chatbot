"""Text chunking utilities that preserve document provenance metadata."""

import logging
import re
from pathlib import Path

from app.rag.types import DocumentChunk, LoadedText

logger = logging.getLogger(__name__)

HEADING_RE = re.compile(r"^(?:[A-Z][A-Z0-9 /&():-]{4,}|[0-9]+(?:\.[0-9]+)*\s+.+)$")


def chunk_loaded_texts(
    loaded_texts: list[LoadedText],
    *,
    document_id: str,
    filename: str,
    source_path: Path,
    upload_time: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    """Split extracted text into overlapping chunks with provenance and statistics.

    Args:
        loaded_texts: Text blocks produced by the document loader.
        document_id: Stable identifier generated for the uploaded document.
        filename: Original uploaded filename shown in citations.
        source_path: Local path where the uploaded source file was saved.
        upload_time: ISO timestamp for the ingestion run.
        chunk_size: Target maximum number of words per chunk.
        chunk_overlap: Number of words repeated between neighboring chunks.

    Returns:
        Searchable DocumentChunk objects with page, section, and statistical metadata.
    """
    if chunk_size <= 0:
        msg = f"Invalid chunk_size config ({chunk_size}). Must be a positive integer."
        raise ValueError(msg)

    chunks: list[DocumentChunk] = []
    global_chunk_index = 0

    logger.info("Starting chunking pipeline for document: %s", filename)

    for item in loaded_texts:
        words = item.text.split()
        if not words:
            continue

        section = item.section or _detect_section(item.text)
        step = max(1, chunk_size - min(chunk_overlap, chunk_size - 1))

        for start in range(0, len(words), step):
            window = words[start : start + chunk_size]
            if not window:
                continue

            global_chunk_index += 1
            page_part = f"p{item.page}" if item.page is not None else "pna"

            chunk_id = f"{document_id}_{page_part}_c{global_chunk_index}"
            raw_text = " ".join(window).strip()
            word_count = len(window)
            char_count = len(raw_text)
            unique_words = {word.lower() for word in window}
            lexical_density = round(len(unique_words) / word_count, 3) if word_count > 0 else 0.0

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename=filename,
                    text=raw_text,
                    page=item.page,
                    section=section,
                    source_path=str(source_path),
                    upload_time=upload_time,
                    metadata={
                        "stat_word_count": word_count,
                        "stat_char_count": char_count,
                        "stat_lexical_density": lexical_density,
                        "stat_chunk_index": global_chunk_index,
                    },
                )
            )
            if start + chunk_size >= len(words):
                break

    logger.info("Successfully generated %d chunks for document: %s", len(chunks), filename)
    return chunks


def _detect_section(text: str) -> str | None:
    """Infer a section heading from early text lines for chunk metadata."""
    for raw_line in text.splitlines()[:12]:
        line = raw_line.strip()
        if 5 <= len(line) <= 90 and HEADING_RE.match(line):
            return line
    return None
