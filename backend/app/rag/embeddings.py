"""Embedding provider implementations for semantic retrieval."""

import hashlib
import math
from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings


class EmbeddingProvider(ABC):
    """Interface implemented by all embedding backends."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed many stored document chunks."""
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed one user query for retrieval."""
        raise NotImplementedError


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic local embeddings for tests and offline demos."""

    def __init__(self, dimension: int = 384) -> None:
        """Create a deterministic local embedding provider."""
        self.dimension = dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed document texts with deterministic hash vectors."""
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        """Embed a query with the same hash-vector method."""
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        """Convert text tokens into a normalized sparse hash vector."""
        vector = [0.0] * self.dimension
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """Embedding provider backed by a local SentenceTransformers model."""

    def __init__(self, model_name: str) -> None:
        """Load a local SentenceTransformer model."""
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed document texts with SentenceTransformers."""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return [embedding.tolist() for embedding in embeddings]

    def embed_query(self, text: str) -> list[float]:
        """Embed a query with SentenceTransformers."""
        embedding = self.model.encode([text], normalize_embeddings=True)[0]
        return embedding.tolist()


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    """Embedding provider that calls an OpenAI-compatible embeddings API."""

    def __init__(self, settings: Settings) -> None:
        """Configure an OpenAI-compatible embedding API client."""
        if not settings.embedding_api_key:
            raise ValueError("EMBEDDING_API_KEY is required for OpenAI-compatible embeddings.")
        self.api_key = settings.embedding_api_key
        self.model = settings.embedding_model
        self.api_base = settings.embedding_api_base.rstrip("/")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed document texts through the remote API."""
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        """Embed one query through the remote API."""
        return self._embed([text])[0]

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Call the OpenAI-compatible embeddings endpoint."""
        response = httpx.post(
            f"{self.api_base}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return [item["embedding"] for item in payload["data"]]


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Select the embedding provider from settings."""
    provider = settings.embedding_provider.lower()
    if provider in {"hash", "mock", "test"}:
        return HashEmbeddingProvider(settings.embedding_dimension)
    if provider in {"openai", "openai-compatible"}:
        return OpenAICompatibleEmbeddingProvider(settings)
    return SentenceTransformerEmbeddingProvider(settings.embedding_model)
