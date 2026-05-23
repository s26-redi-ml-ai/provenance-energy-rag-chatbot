from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.rag.types import LoadedText
from app.utils.text_cleaning import clean_text, strip_markdown


class DocumentLoadingError(ValueError):
    """Raised when a document cannot be safely loaded."""


def load_document(path: Path, filename: str) -> list[LoadedText]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            return _load_pdf(path)
        if suffix == ".docx":
            return _load_docx(path)
        if suffix in {".txt"}:
            return _load_plain_text(path)
        if suffix in {".md", ".markdown"}:
            return _load_markdown(path)
    except DocumentLoadingError:
        raise
    except Exception as exc:  # noqa: BLE001 - convert parser errors into safe API errors
        raise DocumentLoadingError(f"Could not extract text from {filename}.") from exc
    raise DocumentLoadingError(f"Unsupported document type: {suffix}")


def _load_pdf(path: Path) -> list[LoadedText]:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # noqa: BLE001
        raise DocumentLoadingError("The PDF appears to be corrupted or unreadable.") from exc

    pages: list[LoadedText] = []
    for index, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if text:
            pages.append(LoadedText(text=text, page=index))
    if not pages:
        raise DocumentLoadingError(
            "No extractable text was found. Scanned PDFs need OCR, which is future work."
        )
    return pages


def _load_docx(path: Path) -> list[LoadedText]:
    document = DocxDocument(str(path))
    blocks: list[tuple[str, str | None]] = []
    current_section: str | None = None
    section_lines: list[str] = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style_name = paragraph.style.name.lower() if paragraph.style else ""
        if style_name.startswith("heading"):
            if section_lines:
                blocks.append(("\n".join(section_lines), current_section))
                section_lines = []
            current_section = text
            section_lines.append(text)
        else:
            section_lines.append(text)

    if section_lines:
        blocks.append(("\n".join(section_lines), current_section))

    loaded: list[LoadedText] = []
    for block, section in blocks:
        cleaned = clean_text(block)
        if cleaned:
            loaded.append(LoadedText(text=cleaned, page=None, section=section))
    if not loaded:
        raise DocumentLoadingError("No extractable text was found in the DOCX file.")
    return loaded


def _load_plain_text(path: Path) -> list[LoadedText]:
    text = clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    if not text:
        raise DocumentLoadingError("The uploaded text file is empty.")
    return [LoadedText(text=text, page=None)]


def _load_markdown(path: Path) -> list[LoadedText]:
    text = clean_text(strip_markdown(path.read_text(encoding="utf-8", errors="ignore")))
    if not text:
        raise DocumentLoadingError("The uploaded Markdown file is empty.")
    return [LoadedText(text=text, page=None)]
