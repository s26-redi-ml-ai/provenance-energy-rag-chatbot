"""FastAPI dependency helpers for sharing the RAG service instance."""

import threading

from app.core.config import get_settings
from app.rag.service import RAGService

_service: RAGService | None = None
_lock = threading.Lock()


def get_rag_service() -> RAGService:
    """Return a shared RAGService instance for FastAPI dependency injection."""
    global _service
    if _service is None:
        with _lock:
            if _service is None:
                _service = RAGService(get_settings())
    return _service


def reset_rag_service() -> None:
    """Clear the shared service so tests can build a fresh instance."""
    global _service
    with _lock:
        _service = None
