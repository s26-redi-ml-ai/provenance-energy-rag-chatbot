import csv
import logging
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.rag.types import LoadedText
from app.utils.text_cleaning import clean_text, strip_markdown

# Configure logging
logger = logging.getLogger(__name__)
_SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown", ".csv"}

class DocumentLoadingError(ValueError):
    """Raised when a document cannot be safely loaded or parsed."""

def load_document(path: Path, filename: str) -> list[LoadedText]:
    """Load and extract text from a supported document file."""
    suffix = path.suffix.lower()
    logger.info("Loading document: %s (type: %s)", filename, suffix)

    if suffix not in _SUPPORTED_EXTENSIONS:
        allowed_types = ", ".join(sorted(_SUPPORTED_EXTENSIONS))
        raise DocumentLoadingError(
            f"Unsupported file type '{suffix}'. Allowed types: {allowed_types}."
        )

    # Initialize result list
    result: list[LoadedText] = []

    try:
        if suffix == ".pdf":
            result = _load_pdf(path)
        elif suffix == ".docx":
            result = _load_docx(path)
        elif suffix == ".txt":
            result = _load_plain_text(path)
        elif suffix in {".md", ".markdown"}:
            result = _load_markdown(path)
        elif suffix == ".csv":
            result = _load_csv(path)
    except DocumentLoadingError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected parser failure for %s", filename)
        raise DocumentLoadingError(
            f"Could not extract text from '{filename}' due to an internal error."
        ) from exc

    logger.info("Successfully loaded %d block(s) from %s", len(result), filename)
    return result

def _load_pdf(path: Path) -> list[LoadedText]:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise DocumentLoadingError("The PDF file appears to be corrupted.") from exc

    pages: list[LoadedText] = []
    for index, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if text:
            pages.append(LoadedText(text=text, page=index))
    
    if not pages:
        raise DocumentLoadingError("No extractable text found in PDF.")
    return pages

def _load_docx(path: Path) -> list[LoadedText]:
    document = DocxDocument(str(path))
    loaded: list[LoadedText] = []
    for paragraph in document.paragraphs:
        text = clean_text(paragraph.text)
        if text:
            loaded.append(LoadedText(text=text, page=None))
    return loaded

def _load_plain_text(path: Path) -> list[LoadedText]:
    text = clean_text(path.read_text(encoding="utf-8", errors="ignore"))
    return [LoadedText(text=text, page=None)] if text else []

def _load_markdown(path: Path) -> list[LoadedText]:
    text = clean_text(strip_markdown(path.read_text(encoding="utf-8", errors="ignore")))
    return [LoadedText(text=text, page=None)] if text else []

def _load_csv(path: Path) -> list[LoadedText]:
    loaded_rows: list[LoadedText] = []
    with open(path, encoding="utf-8-sig", errors="ignore") as f:
        reader = csv.DictReader(f)
        for index, row in enumerate(reader, start=1):
            row_text = clean_text(", ".join([f"{k}: {v}" for k, v in row.items() if k and v]))
            if row_text:
                loaded_rows.append(LoadedText(text=row_text, page=None, section=f"Row {index}"))
    return loaded_rows