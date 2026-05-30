"""FastAPI application factory and route registration for the RAG backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, documents, fault_codes, upload
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Document-grounded RAG chatbot backend with provenance.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/energy")
    def energy() -> dict[str, str]:
        """Return the project-specific liveness response used by the frontend and tests."""
        return {"status": "ok"}

    @app.get("/health")
    def health() -> dict[str, str]:
        """Return a conventional health-check response for deployment tools."""
        return {"status": "ok"}

    app.include_router(upload.router)
    app.include_router(documents.router)
    app.include_router(chat.router)
    app.include_router(fault_codes.router)
    return app


app = create_app()
