"""Fault-code lookup endpoint for exact code matching without LLM calls."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_rag_service
from app.models.schemas import FaultCodeLookupRequest, FaultCodeLookupResponse
from app.rag.service import RAGService

router = APIRouter(prefix="/fault-codes", tags=["fault-codes"])


@router.post(
    "/lookup",
    response_model=FaultCodeLookupResponse,
    summary="Lookup a fault code",
    description="Searches indexed documents for exact fault code matches without calling the LLM.",
)
def lookup_fault_code(
    request: FaultCodeLookupRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> FaultCodeLookupResponse:
    """Return exact fault-code matches from indexed chunks."""
    return rag_service.lookup_fault_code(request)
