from dataclasses import dataclass


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


@dataclass(frozen=True)
class RetrievedChunk:
    """Document chunk paired with a retrieval score and source type."""

    chunk: DocumentChunk
    relevance_score: float
    source: str = "semantic"
    suggested_tilt_angle: float | None = None
    confidence_level: str = "Medium"
    estimated_irradiation_gain: float | None = None
