import json
import threading
from pathlib import Path

from app.models.schemas import DocumentMetadata


class DocumentRegistry:
    def __init__(self, processed_dir: Path) -> None:
        self.processed_dir = processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.processed_dir / "documents.json"
        self._lock = threading.Lock()

    def upsert(self, metadata: DocumentMetadata) -> None:
        with self._lock:
            documents = self._read()
            documents[metadata.document_id] = metadata.model_dump()
            self._write(documents)

    def list_documents(self) -> list[DocumentMetadata]:
        with self._lock:
            return [
                DocumentMetadata(**item)
                for item in sorted(
                    self._read().values(),
                    key=lambda row: row.get("upload_time", ""),
                    reverse=True,
                )
            ]

    def _read(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write(self, documents: dict[str, dict]) -> None:
        self.path.write_text(json.dumps(documents, indent=2), encoding="utf-8")
