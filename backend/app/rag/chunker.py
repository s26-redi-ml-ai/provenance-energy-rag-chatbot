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
    """Split extracted LoadedText documents into statistically monitored uniform chunks.

    Args:
        loaded_texts: List of LoadedText objects coming directly from the loader.
        document_id: Unique identifier generated for the uploaded document.
        filename: Original name of the processed file.
        source_path: Local system path to the source file.
        upload_time: ISO timestamp representing when the file was processed.
        chunk_size: Target maximum word count for each separate chunk window.
        chunk_overlap: Overlapping word boundary count between adjacent chunks.

    Returns:
        A list of structurally verified and mathematically tracked DocumentChunks.
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
            w_count = len(window)
            c_count = len(raw_text)
            unique_words = {w.lower() for w in window}
            lexical_density = round(len(unique_words) / w_count, 3) if w_count > 0 else 0.0

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
                        "stat_word_count": w_count,
                        "stat_char_count": c_count,
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
    """Scan the initial lines of the text block to infer structural heading metadata."""
    for raw_line in text.splitlines()[:12]:
        line = raw_line.strip()
        if 5 <= len(line) <= 90 and HEADING_RE.match(line):
            return line
    return None
