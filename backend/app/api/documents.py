from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_rag_service
from app.models.schemas import DocumentMetadata
from app.rag.service import RAGService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentMetadata])
def list_documents(
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> list[DocumentMetadata]:
    return rag_service.list_documents()
