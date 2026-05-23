from app.models.schemas import SourceReference
from app.rag.types import RetrievedChunk
from app.utils.text_cleaning import make_snippet


def build_source_references(retrieved: list[RetrievedChunk]) -> list[SourceReference]:
    return [
        SourceReference(
            source_id=f"Source {index}",
            document_id=item.chunk.document_id,
            filename=item.chunk.filename,
            page=item.chunk.page,
            section=item.chunk.section,
            chunk_id=item.chunk.chunk_id,
            relevance_score=round(item.relevance_score, 4),
            text_snippet=make_snippet(item.chunk.text),
            full_text=item.chunk.text,
        )
        for index, item in enumerate(retrieved, start=1)
    ]
