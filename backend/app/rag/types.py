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
    citation_label: str = field(init=False)

    def __post_init__(self):
        page_info = f", p. {self.page}" if self.page is not None else ""
        section_info = f" ({self.section})" if self.section else ""
        citation = f"{self.filename}{page_info}{section_info}"
        object.__setattr__(self, "citation_label", citation)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: DocumentChunk
    relevance_score: float
    source: str = "semantic"
    suggested_tilt_angle: float | None = None
    confidence_level: str = "Medium"
    estimated_irradiation_gain: float | None = None
