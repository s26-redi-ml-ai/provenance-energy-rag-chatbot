"""Tests for the FastAPI application factory and core route registration."""

from app.main import app


def test_energy_endpoint_returns_correct_payload(client):
    """Verify the liveness endpoint returns the expected payload."""
    response = client.get("/energy")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_title_is_configured(client):
    """Verify the FastAPI app title is set correctly."""
    assert app.title is not None
    assert "RAG" in app.title


def test_app_description_is_configured(client):
    """Verify the FastAPI app description is set correctly."""
    assert app.description is not None
    assert len(app.description) > 0
