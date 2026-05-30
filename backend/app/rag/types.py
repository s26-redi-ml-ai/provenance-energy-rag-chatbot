"""Internal dataclasses passed between RAG pipeline stages."""

from dataclasses import dataclass, field

MetadataValue = str | int | float | bool


@dataclass(frozen=True)
class LoadedText:
    """Text extracted from one page or section before chunking."""

    text: str
    page: int | None
    section: str | None = None


@dataclass(frozen=True)
class DocumentChunk:
    """Searchable document fragment with provenance and optional metrics metadata."""

    chunk_id: str
    document_id: str
    filename: str
    text: str
    page: int | None
    section: str | None
    source_path: str
    upload_time: str
    metadata: dict[str, MetadataValue] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedChunk:
    """Document chunk paired with a retrieval score and source type."""

    chunk: DocumentChunk
    relevance_score: float
    source: str = "semantic"
