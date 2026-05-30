"""Pydantic schemas that define backend API contracts."""

from typing import Literal

from pydantic import BaseModel, Field

AnswerMode = Literal["document", "general", "hybrid"]
ConfidenceLevel = Literal["low", "medium", "high"]


class SourceReference(BaseModel):
    """Structured provenance returned with grounded answers."""

    source_id: str
    document_id: str
    filename: str
    page: int | None = None
    section: str | None = None
    chunk_id: str
    relevance_score: float
    text_snippet: str
    full_text: str


class ChatRequest(BaseModel):
    """Input payload for the chat endpoint."""

    question: str = Field(..., min_length=2, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=12)
    conversation_id: str | None = None
    mode: AnswerMode = "document"


class ChatResponse(BaseModel):
    """Output payload from the chat endpoint."""

    answer: str
    grounded: bool
    confidence: ConfidenceLevel
    mode: AnswerMode
    sources: list[SourceReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DocumentMetadata(BaseModel):
    """Stored metadata about an indexed document."""

    document_id: str
    filename: str
    upload_time: str
    chunks_created: int
    status: Literal["indexed", "failed"]
    source_path: str


class UploadResponse(BaseModel):
    """Summary returned after a document is indexed."""

    document_id: str
    filename: str
    chunks_created: int
    status: Literal["indexed"]


class ChunkMetadata(BaseModel):
    """Metadata shape used to describe an indexed text chunk."""

    chunk_id: str
    document_id: str
    filename: str
    page: int | None = None
    section: str | None = None
    source_path: str
    upload_time: str


class FaultCodeLookupRequest(BaseModel):
    """Input payload for exact fault-code lookup."""

    code: str = Field(..., min_length=1, max_length=80)
    top_k: int = Field(default=10, ge=1, le=25)


class FaultCodeMatch(BaseModel):
    """One exact fault-code match returned to the frontend."""

    source_id: str
    document_id: str
    filename: str
    page: int | None = None
    section: str | None = None
    chunk_id: str
    relevance_score: float
    matched_terms: list[str] = Field(default_factory=list)
    text_snippet: str
    full_text: str


class FaultCodeLookupResponse(BaseModel):
    """Output payload for exact fault-code lookup."""

    code: str
    normalized_terms: list[str] = Field(default_factory=list)
    matches: list[FaultCodeMatch] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Simple error response shape for documented failures."""

    detail: str
