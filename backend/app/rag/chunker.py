import re
from pathlib import Path

from app.rag.types import DocumentChunk, LoadedText

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
    chunks: list[DocumentChunk] = []
    per_page_counts: dict[str, int] = {}

    for item in loaded_texts:
        words = item.text.split()
        if not words:
            continue

        page_key = str(item.page or "na")
        section = item.section or _detect_section(item.text)
        step = max(1, chunk_size - min(chunk_overlap, chunk_size - 1))

        for start in range(0, len(words), step):
            window = words[start : start + chunk_size]
            if not window:
                continue
            per_page_counts[page_key] = per_page_counts.get(page_key, 0) + 1
            chunk_index = per_page_counts[page_key]
            page_part = f"p{item.page}" if item.page is not None else "pna"
            chunk_id = f"{document_id}_{page_part}_c{chunk_index}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    filename=filename,
                    text=" ".join(window).strip(),
                    page=item.page,
                    section=section,
                    source_path=str(source_path),
                    upload_time=upload_time,
                )
            )
            if start + chunk_size >= len(words):
                break
    return chunks


def _detect_section(text: str) -> str | None:
    for raw_line in text.splitlines()[:12]:
        line = raw_line.strip()
        if 5 <= len(line) <= 90 and HEADING_RE.match(line):
            return line
    return None
