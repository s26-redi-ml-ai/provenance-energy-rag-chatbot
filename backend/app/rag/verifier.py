"""Answer verification helpers for refusal and citation integrity."""

import re
from typing import Any

CITATION_RE = re.compile(r"\[([^\]]+)\]")
REFUSAL = "I could not find enough information in the uploaded documents to answer this reliably."


def validate_citations(answer: str, source_count: int) -> tuple[str, list[str]]:
    warnings: list[str] = []

    if isinstance(retrieved_chunks, int):
        allowed_sources = {str(i) for i in range(1, retrieved_chunks + 1)}

    def replace(match: re.Match[str]) -> str:
        source_number = match.group(1)
        if source_number in allowed:
            return match.group(0)
        warnings.append(f"Removed hallucinated or unsupported citation [{full_citation}].")
        return ""

    cleaned = CITATION_RE.sub(replace_modern, answer).strip()
    if (
        retrieved_chunks
        and not CITATION_RE.search(cleaned)
        and not is_refusal(cleaned)
        and fallback_label
    ):
        cleaned = f"{cleaned} [{fallback_label}]"
        warnings.append(
            f"Added fallback citation to the strongest retrieved source: [{fallback_label}]."
        )

    return cleaned, warnings


def is_refusal(answer: str) -> bool:
    return REFUSAL.lower() in answer.lower()
