"""Document upload endpoint and file safety validation."""

import re
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import Settings, get_settings
from app.core.dependencies import get_rag_service
from app.models.schemas import UploadResponse
from app.rag.loader import DocumentLoadingError
from app.rag.service import RAGService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="Uploads and indexes a PDF, DOCX, TXT, or Markdown file.",
)
async def upload_document(
    file: Annotated[UploadFile, File(...)],
    settings: Annotated[Settings, Depends(get_settings)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> UploadResponse:
    """Validate, save, and index one uploaded technical document."""
    original_name = Path(file.filename or "").name
    safe_name = _sanitize_filename(original_name)
    extension = Path(safe_name).suffix.lower()

    if not safe_name or extension not in settings.allowed_extensions:
        allowed_types = ", ".join(sorted(settings.allowed_extensions))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed types: {allowed_types}",
        )

    # Read the upload once, then validate size and emptiness before indexing.
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is larger than {settings.max_upload_size_mb} MB.",
        )
    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    saved_path = settings.raw_data_dir / f"{document_id}_{safe_name}"
    saved_path.write_bytes(content)

    try:
        # The RAG service owns extraction, chunking, embeddings, and storage.
        return rag_service.index_file(document_id=document_id, filename=safe_name, path=saved_path)
    except DocumentLoadingError as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document indexing failed.",
        ) from exc


def _sanitize_filename(filename: str) -> str:
    """Convert an uploaded filename into a safe local filename."""
    filename = filename.strip().replace("\\", "_").replace("/", "_")
    filename = re.sub(r"[^A-Za-z0-9._ -]", "_", filename)
    filename = re.sub(r"\s+", "_", filename)
    return filename[:180]
