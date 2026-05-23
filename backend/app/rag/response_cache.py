from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from app.models.schemas import ChatRequest, ChatResponse, DocumentMetadata


class ResponseCache:
    def __init__(self, path: Path, ttl_seconds: int) -> None:
        self.path = path
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def get(self, cache_key: str) -> ChatResponse | None:
        with self._lock, sqlite3.connect(self.path) as connection:
            row = connection.execute(
                "SELECT payload, created_at FROM response_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()

            if row is None:
                return None

            payload, created_at = row
            if self.ttl_seconds > 0 and time.time() - float(created_at) > self.ttl_seconds:
                connection.execute(
                    "DELETE FROM response_cache WHERE cache_key = ?",
                    (cache_key,),
                )
                return None

            return ChatResponse.model_validate_json(payload)

    def set(self, cache_key: str, response: ChatResponse) -> None:
        with self._lock, sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO response_cache (cache_key, payload, created_at)
                VALUES (?, ?, ?)
                """,
                (cache_key, response.model_dump_json(), time.time()),
            )

    def clear(self) -> None:
        with self._lock, sqlite3.connect(self.path) as connection:
            connection.execute("DELETE FROM response_cache")

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS response_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )


def document_fingerprint(documents: list[DocumentMetadata]) -> str:
    payload = [
        {
            "document_id": document.document_id,
            "filename": document.filename,
            "upload_time": document.upload_time,
            "chunks_created": document.chunks_created,
            "status": document.status,
        }
        for document in documents
    ]
    return _hash_json(payload)


def build_cache_key(
    *,
    request: ChatRequest,
    document_fingerprint_value: str,
    settings_fingerprint: dict[str, Any],
) -> str:
    normalized_question = " ".join(request.question.lower().split())
    payload = {
        "question": normalized_question,
        "top_k": request.top_k,
        "mode": request.mode,
        "documents": document_fingerprint_value,
        "settings": settings_fingerprint,
    }
    return _hash_json(payload)


def _hash_json(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
