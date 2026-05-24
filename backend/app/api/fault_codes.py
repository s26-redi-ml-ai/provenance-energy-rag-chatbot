from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import get_rag_service
from app.models.schemas import FaultCodeLookupRequest, FaultCodeLookupResponse
from app.rag.service import RAGService

router = APIRouter(prefix="/fault-codes", tags=["fault-codes"])


@router.post("/lookup", response_model=FaultCodeLookupResponse)
def lookup_fault_code(
    request: FaultCodeLookupRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> FaultCodeLookupResponse:
    return rag_service.lookup_fault_code(request)
