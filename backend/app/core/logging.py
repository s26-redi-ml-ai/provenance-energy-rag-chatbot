"""Logging setup used when the FastAPI app starts."""

import logging


def configure_logging() -> None:
    """Configure basic application logging for local development."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
