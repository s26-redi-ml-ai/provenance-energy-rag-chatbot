import logging
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.rag.types import LoadedText
from app.utils.text_cleaning import clean_text, strip_markdown

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}


class DocumentLoadingError(ValueError):
    """Raised when a document cannot be safely loaded or parsed."""


def load_document(path: Path, filename: str) -> list[LoadedText]:
    """Load and extract text from a supported document file.

    Routes to the appropriate parser based on file extension and returns
    a list of LoadedText objects preserving page and section metadata.

    Args:
        path: Absolute path to the saved file on disk.
        filename: Original upload filename, used only for error messages.

    Returns:
        Non-empty list of LoadedText objects extracted from the document.

    Raises:
        DocumentLoadingError: If the file type is unsupported, the file is
            empty or unreadable, or an internal parser error occurs.
    """
    suffix = path.suffix.lower()
    logger.info("Loading document: %s (type: %s)", filename, suffix)

    if suffix not in _SUPPORTED_EXTENSIONS:
        raise DocumentLoadingError(
            "Unsupported file type '%s'. Allowed types: %s."
            % (suffix, ", ".join(sorted(_SUPPORTED_EXTENSIONS)))
        )

    try:
        if suffix == ".pdf":
            result = _load_pdf(path)
        elif suffix == ".docx":
            result = _load_docx(path)
        elif suffix == ".txt":
            result = _load_plain_text(path)
        else:  # .md / .markdown
            result = _load_markdown(path)
    except DocumentLoadingError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected parser failure for %s", filename)
        raise DocumentLoadingError(
            "Could not extract text from '%s' due to an internal error." % filename
        ) from exc

    logger.info(
        "Successfully loaded %d block(s) from %s", len(result), filename
    )
    return result


def _load_pdf(path: Path) -> list[LoadedText]:
    """Extract text from a PDF, preserving page numbers.

    Uses an adaptive approach: extracts digital text layers first,
    and automatically falls back to OCR if the document is scanned.
    """
    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # noqa: BLE001
        raise DocumentLoadingError(
            "The PDF file appears to be corrupted or unreadable."
        ) from exc

    pages: list[LoadedText] = []
    total_pages = len(reader.pages)


    for index, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        text = clean_text(raw)
        if text:
            pages.append(LoadedText(text=text, page=index))
        else:
            logger.debug("Page %d/%d yielded no digital text, checking for OCR.", index, total_pages)


    if not pages:
        logger.info("No digital text layer detected in '%s'. Falling back to OCR processing...", path.name)
        pages = _execute_pdf_ocr(path)

    if not pages:
        raise DocumentLoadingError(
            "No extractable text was found in the PDF, even after applying OCR processing."
        )

    logger.debug("Extracted text from %d/%d PDF page(s).", len(pages), total_pages)
    return pages


def _execute_pdf_ocr(path: Path) -> list[LoadedText]:
    """Convert PDF pages into high-resolution images and run Tesseract OCR.

    Uses soft imports to maintain environment stability across team machines.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
    except ImportError:
        logger.critical("OCR dependencies (pytesseract/pdf2image) are missing in the local environment.")
        raise DocumentLoadingError(
            "This document is a scanned PDF and requires OCR tools. Please install 'tesseract' and 'poppler'."
        )

    ocr_pages: list[LoadedText] = []
    try:
        images = convert_from_path(str(path), dpi=200)
        
        for index, img in enumerate(images, start=1):
            raw_ocr_text = pytesseract.image_to_string(img, lang="eng")
            cleaned_ocr = clean_text(raw_ocr_text)
            if cleaned_ocr:
                ocr_pages.append(LoadedText(text=cleaned_ocr, page=index))
                
        logger.info("Successfully completed OCR processing for %d page(s) of '%s'", len(ocr_pages), path.name)
    except Exception as ocr_exc:
        logger.error("OCR execution pipeline failed for %s: %s", path.name, str(ocr_exc))
        raise DocumentLoadingError("Failed to extract text from scanned PDF via OCR: %s" % str(ocr_exc)) from ocr_exc

    return ocr_pages


def _load_docx(path: Path) -> list[LoadedText]:
    """Extract text from a Word document, grouping paragraphs by heading sections."""
    try:
        document = DocxDocument(str(path))
    except Exception as exc:  # noqa: BLE001
        raise DocumentLoadingError(
            "The DOCX file appears to be corrupted or unreadable."
        ) from exc

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
    for block_text, section in blocks:
        cleaned = clean_text(block_text)
        if cleaned:
            loaded.append(LoadedText(text=cleaned, page=None, section=section))

    if not loaded:
        raise DocumentLoadingError(
            "No extractable text was found in the DOCX file."
        )

    logger.debug("Extracted %d section block(s) from DOCX.", len(loaded))
    return loaded


def _load_plain_text(path: Path) -> list[LoadedText]:
    """Read a plain text file with UTF-8 encoding, ignoring undecodable bytes."""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(raw)
    if not text:
        raise DocumentLoadingError("The uploaded text file is empty or contains no readable content.")
    return [LoadedText(text=text, page=None)]


def _load_markdown(path: Path) -> list[LoadedText]:
    """Read a Markdown file and strip syntax tokens before returning clean text."""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(strip_markdown(raw))
    if not text:
        raise DocumentLoadingError("The uploaded Markdown file is empty or contains no readable content.")
    return [LoadedText(text=text, page=None)]