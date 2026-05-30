"""Vector-store adapters for in-memory tests and persistent ChromaDB."""

import math
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.rag.types import DocumentChunk, RetrievedChunk


class VectorStore(ABC):
    """Interface shared by all vector-store implementations."""

    @abstractmethod
    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        """Store chunks and their embeddings."""
        raise NotImplementedError

    @abstractmethod
    def semantic_search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        """Find chunks similar to a query embedding."""
        raise NotImplementedError

    @abstractmethod
    def keyword_search(self, terms: list[str], top_k: int) -> list[RetrievedChunk]:
        """Find chunks containing exact keyword terms."""
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """Simple vector store kept in process memory for fast tests."""

    def __init__(self) -> None:
        """Create an empty in-memory store for tests."""
        self._rows: list[tuple[DocumentChunk, list[float]]] = []

    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        """Store or replace chunks in memory."""
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            self._rows = [row for row in self._rows if row[0].chunk_id != chunk.chunk_id]
            self._rows.append((chunk, embedding))

    def semantic_search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        """Search in-memory rows with cosine similarity."""
        scored = [
            RetrievedChunk(chunk=chunk, relevance_score=_cosine(query_embedding, embedding))
            for chunk, embedding in self._rows
        ]
        return sorted(scored, key=lambda item: item.relevance_score, reverse=True)[:top_k]

    def keyword_search(self, terms: list[str], top_k: int) -> list[RetrievedChunk]:
        """Search in-memory rows for exact terms."""
        lowered_terms = [term.lower() for term in terms]
        matches: list[RetrievedChunk] = []
        for chunk, _embedding in self._rows:
            text = chunk.text.lower()
            if any(term in text for term in lowered_terms):
                matches.append(RetrievedChunk(chunk=chunk, relevance_score=0.96, source="keyword"))
        return matches[:top_k]


class ChromaVectorStore(VectorStore):
    """Persistent ChromaDB-backed vector store used by the real app."""

    def __init__(self, settings: Settings) -> None:
        """Open or create a persistent ChromaDB collection."""
        import chromadb

        Path(settings.resolved_vector_store_path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(settings.resolved_vector_store_path))
        self.collection = self.client.get_or_create_collection(
            name=settings.vector_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        """Upsert chunks, embeddings, and metadata into ChromaDB."""
        if not chunks:
            return
        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[_metadata_from_chunk(chunk) for chunk in chunks],
        )

    def semantic_search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        """Query ChromaDB by embedding similarity."""
        if self.collection.count() == 0:
            return []
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        return _retrieved_from_chroma(results)

    def keyword_search(self, terms: list[str], top_k: int) -> list[RetrievedChunk]:
        """Scan ChromaDB documents for exact keyword matches."""
        if not terms or self.collection.count() == 0:
            return []
        rows = self.collection.get(include=["documents", "metadatas"])
        lowered_terms = [term.lower() for term in terms]
        matches: list[RetrievedChunk] = []
        documents = rows.get("documents", [])
        metadatas = rows.get("metadatas", [])
        for document, metadata in zip(documents, metadatas, strict=False):
            if document and any(term in document.lower() for term in lowered_terms):
                matches.append(
                    RetrievedChunk(
                        chunk=_chunk_from_metadata(metadata or {}, document),
                        relevance_score=0.96,
                        source="keyword",
                    )
                )
        return matches[:top_k]


def create_vector_store(settings: Settings) -> VectorStore:
    """Select a vector-store implementation from settings."""
    if settings.vector_store_provider.lower() in {"memory", "in-memory", "test"}:
        return InMemoryVectorStore()
    return ChromaVectorStore(settings)


def _metadata_from_chunk(chunk: DocumentChunk) -> dict[str, str | int | float | bool]:
    """Flatten a DocumentChunk into Chroma-compatible metadata."""
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "filename": chunk.filename,
        "page": chunk.page if chunk.page is not None else -1,
        "section": chunk.section or "",
        "source_path": chunk.source_path,
        "upload_time": chunk.upload_time,
        **chunk.metadata,
    }


def _chunk_from_metadata(metadata: dict[str, Any], text: str) -> DocumentChunk:
    """Rebuild a DocumentChunk from Chroma metadata and text."""
    page = metadata.get("page")
    known_keys = {
        "chunk_id",
        "document_id",
        "filename",
        "page",
        "section",
        "source_path",
        "upload_time",
    }
    extra_metadata = {
        str(key): value
        for key, value in metadata.items()
        if key not in known_keys and isinstance(value, str | int | float | bool)
    }
    return DocumentChunk(
        chunk_id=str(metadata.get("chunk_id", "")),
        document_id=str(metadata.get("document_id", "")),
        filename=str(metadata.get("filename", "")),
        text=text,
        page=None if page in {None, "", -1} else int(page),
        section=str(metadata.get("section") or "") or None,
        source_path=str(metadata.get("source_path", "")),
        upload_time=str(metadata.get("upload_time", "")),
        metadata=extra_metadata,
    )


def _retrieved_from_chroma(results: dict[str, Any]) -> list[RetrievedChunk]:
    """Convert raw Chroma query results into RetrievedChunk objects."""
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved: list[RetrievedChunk] = []
    for document, metadata, distance in zip(documents, metadatas, distances, strict=False):
        score = max(0.0, min(1.0, 1.0 - float(distance)))
        retrieved.append(
            RetrievedChunk(
                chunk=_chunk_from_metadata(metadata or {}, document or ""),
                relevance_score=score,
            )
        )
    return retrieved


def _cosine(left: list[float], right: list[float]) -> float:
    """Compute bounded cosine similarity for in-memory retrieval."""
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(0.0, min(1.0, numerator / (left_norm * right_norm)))
