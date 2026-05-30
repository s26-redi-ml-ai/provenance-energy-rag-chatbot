"""Retriever that combines semantic search with exact fault-code matching."""

import re

from app.core.config import Settings
from app.rag.embeddings import EmbeddingProvider
from app.rag.types import RetrievedChunk
from app.rag.vector_store import VectorStore

FAULT_CONTEXT_RE = re.compile(r"\b(fault|error|alarm|code|warning|f\d{1,3})\b", re.IGNORECASE)
FAULT_CODE_RE = re.compile(
    r"\b(?:fault|error|alarm|warning|code)?\s*[-#: ]*\s*([A-Z]?\d{1,3})\b",
    re.IGNORECASE,
)
COMPACT_CODE_RE = re.compile(r"\b([A-Z]\d{1,3})\b", re.IGNORECASE)


class Retriever:
    """Coordinates semantic retrieval and exact-code keyword retrieval."""

    def __init__(
        self,
        *,
        settings: Settings,
        embeddings: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        """Store retriever dependencies from the service layer."""
        self.settings = settings
        self.embeddings = embeddings
        self.vector_store = vector_store

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """Find the strongest evidence chunks for a user question."""
        limit = top_k or self.settings.top_k
        query_embedding = self.embeddings.embed_query(question)
        semantic = self.vector_store.semantic_search(query_embedding, top_k=max(limit * 2, limit))
        semantic = [
            item for item in semantic if item.relevance_score >= self.settings.similarity_threshold
        ]

        exact_terms = extract_exact_terms(question)
        keyword = self.vector_store.keyword_search(exact_terms, top_k=limit) if exact_terms else []

        merged: dict[str, RetrievedChunk] = {}
        for item in semantic + keyword:
            existing = merged.get(item.chunk.chunk_id)
            if existing is None or item.relevance_score > existing.relevance_score:
                merged[item.chunk.chunk_id] = item

        return sorted(merged.values(), key=lambda item: item.relevance_score, reverse=True)[:limit]


def extract_exact_terms(question: str) -> list[str]:
    """Extract possible fault-code variants from a user question."""
    if not FAULT_CONTEXT_RE.search(question):
        return []

    terms: set[str] = set()
    for match in FAULT_CODE_RE.finditer(question):
        raw = match.group(1).upper()
        if raw.isdigit():
            terms.add(raw)
            terms.add(raw.zfill(2))
            terms.add(f"F{raw.zfill(2)}")
            terms.add(f"Fault code {raw.zfill(2)}")
            terms.add(f"Error {raw.zfill(2)}")
        else:
            terms.add(raw)
            numeric = re.sub(r"\D", "", raw)
            if numeric:
                terms.add(numeric.zfill(2))
                terms.add(f"Fault code {numeric.zfill(2)}")

    for match in COMPACT_CODE_RE.finditer(question):
        raw = match.group(1).upper()
        terms.add(raw)
        numeric = re.sub(r"\D", "", raw)
        if numeric:
            terms.add(numeric.zfill(2))

    return sorted(terms)
