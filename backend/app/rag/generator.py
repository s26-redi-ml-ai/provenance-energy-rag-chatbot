"""LLM answer generation providers and offline mock generation."""

import re
from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings


class GenerationError(RuntimeError):
    """Raised when the configured LLM provider cannot generate an answer."""


class AnswerGenerator(ABC):
    """Interface implemented by all answer generators."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate an answer from a fully built prompt."""
        raise NotImplementedError


class MockGenerator(AnswerGenerator):
    """Offline generator used for tests and demos without API keys."""

    def generate(self, prompt: str) -> str:
        """Create a deterministic answer for tests and offline demos."""
        if "General knowledge mode is enabled" in prompt:
            question = _extract_after(prompt, "Question:").strip()
            return (
                "This answer is based on general knowledge and not directly on the uploaded "
                f"documents. For {question}, consult the manufacturer manual and a qualified "
                "technician before taking action."
            )

        source_text = _extract_source_text(prompt)
        if not source_text:
            return (
                "I could not find enough information in the uploaded documents to "
                "answer this reliably."
            )

        first_sentence = _first_sentence(source_text)
        return (
            f"{first_sentence} [Source 1]\n\n"
            "Safety note: follow the manufacturer safety instructions and qualified technician "
            "procedures before performing electrical troubleshooting."
        )


class OpenAICompatibleGenerator(AnswerGenerator):
    """Generator that calls an OpenAI-compatible chat completion API."""

    def __init__(self, settings: Settings) -> None:
        """Configure an OpenAI-compatible chat completion client."""
        if not settings.llm_api_key:
            raise GenerationError("LLM_API_KEY is required for OpenAI-compatible generation.")
        self.api_key = settings.llm_api_key
        self.api_base = settings.llm_api_base.rstrip("/")
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature

    def generate(self, prompt: str) -> str:
        """Call the configured LLM and return its answer text."""
        response = httpx.post(
            f"{self.api_base}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
            },
            timeout=60,
        )
        if response.status_code >= 400:
            raise GenerationError(f"LLM provider returned HTTP {response.status_code}.")
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()


def create_generator(settings: Settings) -> AnswerGenerator:
    """Select the answer generator from settings."""
    provider = settings.llm_provider.lower()
    if provider in {"mock", "test", "offline"}:
        return MockGenerator()
    if provider in {"openai", "openai-compatible", "groq"}:
        return OpenAICompatibleGenerator(settings)
    raise GenerationError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def _extract_source_text(prompt: str) -> str:
    """Pull the first context text block from a grounded prompt."""
    match = re.search(r'Text:\s*\n"(.+?)"', prompt, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_after(text: str, marker: str) -> str:
    """Return prompt text after a marker string."""
    if marker not in text:
        return text
    return text.split(marker, maxsplit=1)[1]


def _first_sentence(text: str) -> str:
    """Return a concise first sentence for mock answers."""
    compact = re.sub(r"\s+", " ", text).strip()
    if not compact:
        return ""
    match = re.search(r"(.+?[.!?])(?:\s|$)", compact)
    if match:
        return match.group(1).strip()
    return compact[:350].strip()
