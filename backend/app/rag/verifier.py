import re
from typing import Any

CITATION_RE = re.compile(r"\[([^\]]+)\]")
REFUSAL = "I could not find enough information in the uploaded documents to answer this reliably."


def _get_fallback_label(chunk: Any) -> str:
    """Safely extract or dynamically build a citation label from a chunk object."""
    if hasattr(chunk, "citation_label") and chunk.citation_label:
        return chunk.citation_label
    filename = getattr(chunk, "filename", "document.txt")
    page = getattr(chunk, "page", None)
    section = getattr(chunk, "section", None)

    page_info = f", p. {page}" if page is not None else ""
    section_info = f" ({section})" if section else ""
    return f"{filename}{page_info}{section_info}"


def validate_citations(
    answer: str, retrieved_chunks: list[Any] | int
) -> tuple[str, list[str]]:
    """Verify that the LLM only cited files or sources that were actually retrieved."""
    warnings: list[str] = []

    if isinstance(retrieved_chunks, int):
        allowed_sources = {str(i) for i in range(1, retrieved_chunks + 1)}

        def replace_legacy(match: re.Match[str]) -> str:
            source_content = match.group(1).strip()
            num_match = re.search(r"\d+", source_content)
            if num_match and num_match.group(0) in allowed_sources:
                return match.group(0)
            warnings.append(f"Removed unsupported citation [{source_content}].")
            return ""

        cleaned = CITATION_RE.sub(replace_legacy, answer).strip()
        fallback_label = "Source 1" if retrieved_chunks > 0 else ""
        
        has_chunks = retrieved_chunks > 0
        has_no_citation = not CITATION_RE.search(cleaned)
        if has_chunks and has_no_citation and not is_refusal(cleaned) and fallback_label:
            cleaned = f"{cleaned} [{fallback_label}]"
            warnings.append(
                f"Added fallback citation to the strongest retrieved source: "
                f"[{fallback_label}]."
            )
        return cleaned, warnings

    allowed_filenames = set()
    allowed_labels = set()
    fallback_label = ""

    if retrieved_chunks:
        first_item = retrieved_chunks[0]
        first_actual = first_item.chunk if hasattr(first_item, "chunk") else first_item
        fallback_label = _get_fallback_label(first_actual)

        for item in retrieved_chunks:
            actual_chunk = item.chunk if hasattr(item, "chunk") else item
            fname = getattr(actual_chunk, "filename", "")
            if fname:
                allowed_filenames.add(fname.lower())
            label = _get_fallback_label(actual_chunk)
            allowed_labels.add(label.lower())

    def replace_modern(match: re.Match[str]) -> str:
        full_citation = match.group(1).strip()
        filename_part = full_citation.split(",")[0].strip().lower()
        if (
            "source" in filename_part
            or filename_part in allowed_filenames
            or full_citation.lower() in allowed_labels
        ):
            return match.group(0)
        warnings.append(f"Removed hallucinated or unsupported citation [{full_citation}].")
        return ""

    cleaned = CITATION_RE.sub(replace_modern, answer).strip()
    
    has_chunks_list = len(retrieved_chunks) > 0
    has_no_citation_list = not CITATION_RE.search(cleaned)
    if (
        has_chunks_list 
        and has_no_citation_list 
        and not is_refusal(cleaned) 
        and fallback_label
    ):
        cleaned = f"{cleaned} [{fallback_label}]"
        warnings.append(
            f"Added fallback citation to the strongest retrieved source: "
            f"[{fallback_label}]."
        )

    return cleaned, warnings


def is_refusal(answer: str) -> bool:
    """Check if the answer represents a technical refusal due to lack of information."""
    return REFUSAL.lower() in answer.lower() or "cannot find this error" in answer.lower()