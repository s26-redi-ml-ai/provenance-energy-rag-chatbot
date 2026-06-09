from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.rag.types import LoadedText
from app.utils.text_cleaning import clean_text, strip_markdown


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
        allowed_types = ", ".join(sorted(_SUPPORTED_EXTENSIONS))
        raise DocumentLoadingError(
            f"Unsupported file type '{suffix}'. Allowed types: {allowed_types}."
        )

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
    except Exception as exc:  # noqa: BLE001
        raise DocumentLoadingError("The PDF file appears to be corrupted or unreadable.") from exc

    pages: list[LoadedText] = []
    total_pages = len(reader.pages)

    for index, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        text = clean_text(raw)
        if text:
            pages.append(LoadedText(text=text, page=index))
        else:
            logger.debug(
                "Page %d/%d yielded no digital text, checking for OCR.",
                index,
                total_pages,
            )

    if not pages:
        logger.info(
            "No digital text layer detected in '%s'. Falling back to OCR processing...",
            path.name,
        )
        pages = _execute_pdf_ocr(path)

    if not pages:
        raise DocumentLoadingError(
            "No extractable text was found in the PDF, even after applying OCR processing."
        )

    logger.debug("Extracted text from %d/%d PDF page(s).", len(pages), total_pages)
    return pages


def _load_docx(path: Path) -> list[LoadedText]:
    """Extract text from a Word document, grouping paragraphs by heading sections."""
    try:
        document = DocxDocument(str(path))
    except Exception as exc:  # noqa: BLE001
        raise DocumentLoadingError("The DOCX file appears to be corrupted or unreadable.") from exc

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
        raise DocumentLoadingError("No extractable text was found in the DOCX file.")

    logger.debug("Extracted %d section block(s) from DOCX.", len(loaded))
    return loaded


def _load_plain_text(path: Path) -> list[LoadedText]:
    """Read a plain text file with UTF-8 encoding, ignoring undecodable bytes."""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(raw)
    if not text:
        raise DocumentLoadingError(
            "The uploaded text file is empty or contains no readable content."
        )
    return [LoadedText(text=text, page=None)]


def _load_markdown(path: Path) -> list[LoadedText]:
    """Read a Markdown file and strip syntax tokens before returning clean text."""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(strip_markdown(raw))
    if not text:
        raise DocumentLoadingError(
            "The uploaded Markdown file is empty or contains no readable content."
        )
    return [LoadedText(text=text, page=None)]


def _load_csv(path: Path) -> list[LoadedText]:
    """Extract and structure data from a CSV file, treating rows as individual semantic texts."""
    loaded_rows: list[LoadedText] = []

    try:
        with open(path, encoding="utf-8-sig", errors="ignore") as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                raise DocumentLoadingError("The uploaded CSV file is missing column headers.")

            for index, row in enumerate(reader, start=1):
                row_parts = []
                for key, value in row.items():
                    if key and value:
                        row_parts.append(f"{key.strip()}: {value.strip()}")

                if not row_parts:
                    continue

                row_text = clean_text(", ".join(row_parts))

                if row_text:
                    loaded_rows.append(LoadedText(text=row_text, page=None, section=f"Row {index}"))

    except DocumentLoadingError:
        raise
    except Exception as exc:
        raise DocumentLoadingError(f"Failed to parse CSV structured data: {str(exc)}") from exc

    if not loaded_rows:
        raise DocumentLoadingError("The uploaded CSV file contains no readable data rows.")

    logger.debug("Extracted %d structured data row(s) from CSV.", len(loaded_rows))
    return loaded_rows
