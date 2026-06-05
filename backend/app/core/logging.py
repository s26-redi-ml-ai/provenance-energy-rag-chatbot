"""Logging setup used when the FastAPI app starts."""

import logging

_QUIET_LOGGERS = {
    "httpcore": logging.WARNING,
    "httpx": logging.WARNING,
    "huggingface_hub": logging.WARNING,
    "sentence_transformers": logging.WARNING,
    "transformers": logging.WARNING,
    "watchfiles": logging.WARNING,
}


def configure_logging() -> None:
    """Configure application logging and quiet noisy third-party libraries."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    for logger_name, level in _QUIET_LOGGERS.items():
        logging.getLogger(logger_name).setLevel(level)
