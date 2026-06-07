"""Logging setup used when the FastAPI app starts."""

import logging
import os
import warnings

_QUIET_LOGGERS = {
    "httpcore": logging.WARNING,
    "httpx": logging.WARNING,
    "huggingface_hub": logging.ERROR,
    "huggingface_hub.utils._http": logging.ERROR,
    "sentence_transformers": logging.WARNING,
    "transformers": logging.WARNING,
    "watchfiles": logging.WARNING,
}

_WARNING_PATTERNS_TO_HIDE = (r".*unauthenticated requests to the HF Hub.*",)


def configure_logging() -> None:
    """Configure application logging and quiet noisy third-party libraries."""
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    for logger_name, level in _QUIET_LOGGERS.items():
        logging.getLogger(logger_name).setLevel(level)

    for warning_pattern in _WARNING_PATTERNS_TO_HIDE:
        warnings.filterwarnings("ignore", message=warning_pattern)
