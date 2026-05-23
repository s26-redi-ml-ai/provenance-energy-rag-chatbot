import re

CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
MULTIPLE_SPACES = re.compile(r"[ \t]+")
MULTIPLE_BLANK_LINES = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    """Normalize extracted manual text while preserving paragraph boundaries."""
    text = CONTROL_CHARS.sub(" ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = "\n".join(MULTIPLE_SPACES.sub(" ", line).strip() for line in text.splitlines())
    text = MULTIPLE_BLANK_LINES.sub("\n\n", text)
    return text.strip()


def make_snippet(text: str, max_chars: int = 420) -> str:
    compact = MULTIPLE_SPACES.sub(" ", text.replace("\n", " ")).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~>#-]{2,}", " ", text)
    return text
