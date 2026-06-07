"""Shared pytest fixtures for isolated backend tests."""

import importlib
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def isolated_backend_state(tmp_path, monkeypatch):
    """Give every test a clean backend state and temporary runtime data folder."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("VECTOR_STORE_PROVIDER", "memory")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "hash")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("SIMILARITY_THRESHOLD", "0.35")
    monkeypatch.setenv("ALLOW_GENERAL_KNOWLEDGE", "true")

    config = importlib.import_module("app.core.config")
    dependencies = importlib.import_module("app.core.dependencies")
    config.get_settings.cache_clear()
    dependencies.reset_rag_service()

    yield

    config.get_settings.cache_clear()
    dependencies.reset_rag_service()


@pytest.fixture()
def client() -> TestClient:
    """Create a FastAPI test client after the isolated settings are installed."""
    main = importlib.import_module("app.main")
    test_app = main.create_app()
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture()
def fault_manual_text() -> str:
    """Return a reusable small manual containing realistic fault-code evidence."""
    return (
        "Fault Codes\n\n"
        "Fault code 07: Overload timeout. Recommended action: reduce the connected load, "
        "restart the inverter, and check whether the fault clears.\n\n"
        "Fault code F12: DC bus over-voltage. Stop operation and inspect the PV input.\n\n"
        "Maintenance: inspect terminals only after isolating the system."
    )


@pytest.fixture()
def upload_text_document(client: TestClient) -> Callable[[str, str], dict]:
    """Upload a TXT document and return the successful upload response payload."""

    def _upload(filename: str, text: str) -> dict:
        response = client.post(
            "/documents/upload",
            files={"file": (filename, text.encode("utf-8"), "text/plain")},
        )
        assert response.status_code == 201
        return response.json()

    return _upload
