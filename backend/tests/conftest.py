import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("VECTOR_STORE_PROVIDER", "memory")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("SIMILARITY_THRESHOLD", "0.35")
    monkeypatch.setenv("ALLOW_GENERAL_KNOWLEDGE", "false")

    config = importlib.import_module("app.core.config")
    dependencies = importlib.import_module("app.core.dependencies")
    config.get_settings.cache_clear()
    dependencies.reset_rag_service()

    main = importlib.import_module("app.main")
    test_app = main.create_app()
    with TestClient(test_app) as test_client:
        yield test_client

    config.get_settings.cache_clear()
    dependencies.reset_rag_service()
