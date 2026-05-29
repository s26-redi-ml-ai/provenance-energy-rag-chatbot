from dataclasses import dataclass, field

MetadataValue = str | int | float | bool


@dataclass(frozen=True)
class LoadedText:
    text: str
    page: int | None
    section: str | None = None


@dataclass(frozen=True)
class DocumentChunk:
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
    chunk: DocumentChunk
    relevance_score: float
    source: str = "semantic"
