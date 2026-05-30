"""Answer verification helpers for refusal and citation integrity."""

import re

CITATION_RE = re.compile(r"\[Source\s+(\d+)\]")
REFUSAL = "I could not find enough information in the uploaded documents to answer this reliably."


def validate_citations(answer: str, source_count: int) -> tuple[str, list[str]]:
    """Remove unsupported citations and ensure grounded answers cite evidence."""
    warnings: list[str] = []
    allowed = {str(index) for index in range(1, source_count + 1)}

    def replace(match: re.Match[str]) -> str:
        """Keep valid source IDs and strip citations that were not retrieved."""
        source_number = match.group(1)
        if source_number in allowed:
            return match.group(0)
        warnings.append(f"Removed unsupported citation [Source {source_number}].")
        return ""

    cleaned = CITATION_RE.sub(replace, answer).strip()

    if source_count > 0 and not CITATION_RE.search(cleaned) and REFUSAL not in cleaned:
        cleaned = f"{cleaned} [Source 1]"
        warnings.append("Added citation to the strongest retrieved source.")

    return cleaned, warnings


def is_refusal(answer: str) -> bool:
    """Return whether an answer is the standard insufficient-evidence refusal."""
    return REFUSAL.lower() in answer.lower()
