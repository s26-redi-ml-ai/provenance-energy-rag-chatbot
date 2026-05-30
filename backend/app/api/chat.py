"""Chat endpoint that forwards user questions to the RAG service."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_rag_service
from app.models.schemas import ChatRequest, ChatResponse
from app.rag.service import RAGService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> ChatResponse:
    """Answer a user question by delegating to the RAG service."""
    return rag_service.chat(request)
