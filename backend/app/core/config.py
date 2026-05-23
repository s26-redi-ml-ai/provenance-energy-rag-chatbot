from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Trustworthy RAG Chatbot"
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    data_dir: Path = Path("data")
    vector_store_path: Path | None = None
    vector_store_provider: str = "chroma"
    vector_collection_name: str = "technical_manual_chunks"

    llm_provider: str = "mock"
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_api_base: str = "https://api.openai.com/v1"
    llm_temperature: float = 0.0

    embedding_provider: str = "sentence-transformers"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_api_key: str | None = None
    embedding_api_base: str = "https://api.openai.com/v1"
    embedding_dimension: int = 384

    chunk_size: int = 750
    chunk_overlap: int = 150
    top_k: int = 5
    similarity_threshold: float = 0.35
    allow_general_knowledge: bool = False

    response_cache_enabled: bool = True
    response_cache_ttl_seconds: int = 604800

    max_upload_size_mb: int = 25
    allowed_file_types: str = ".pdf,.docx,.txt,.md,.markdown"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_must_be_smaller_than_chunk_size(cls, value: int) -> int:
        if value < 0:
            raise ValueError("CHUNK_OVERLAP must be non-negative")
        return value

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_data_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def resolved_vector_store_path(self) -> Path:
        return self.vector_store_path or self.data_dir / "vector_store"

    @property
    def allowed_extensions(self) -> set[str]:
        return {item.strip().lower() for item in self.allowed_file_types.split(",") if item.strip()}

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # ADD THIS LINE FOR DEBUGGING:
    print(f"\n🚀 DEBUG: Active LLM Provider is set to -> {settings.llm_provider}\n")
    return settings
