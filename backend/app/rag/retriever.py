import math
import re
from dataclasses import replace

from app.core.config import Settings
from app.rag.embeddings import EmbeddingProvider
from app.rag.types import RetrievedChunk
from app.rag.vector_store import VectorStore

FAULT_CONTEXT_RE = re.compile(
    r"\b(fault|error|alarm|code|warning|f\d{1,3}|row|id|status)\b",
    re.IGNORECASE,
)
FAULT_CODE_RE = re.compile(
    r"\b(?:fault|error|alarm|warning|code|row|id)?\s*[-#: ]*\s*([A-Z]?\d{1,3})\b",
    re.IGNORECASE,
)
COMPACT_CODE_RE = re.compile(r"\b([A-Z]\d{1,3})\b", re.IGNORECASE)


class Retriever:
    def __init__(
        self,
        *,
        settings: Settings,
        embeddings: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self.settings = settings
        self.embeddings = embeddings
        self.vector_store = vector_store

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedChunk]:
        limit = top_k or self.settings.top_k
        query_embedding = self.embeddings.embed_query(question)
        semantic = self.vector_store.semantic_search(query_embedding, top_k=max(limit * 2, limit))
        semantic = [
            item
            for item in semantic
            if item.relevance_score >= self.settings.similarity_threshold
        ]

        exact_terms = extract_exact_terms(question)
        keyword = (
            self.vector_store.keyword_search(exact_terms, top_k=limit) if exact_terms else []
        )

        merged: dict[str, RetrievedChunk] = {}
        for item in semantic + keyword:
            existing = merged.get(item.chunk.chunk_id)
            if existing is None or item.relevance_score > existing.relevance_score:
                merged[item.chunk.chunk_id] = item

        sorted_results = sorted(
            merged.values(),
            key=lambda item: item.relevance_score,
            reverse=True,
        )[:limit]

        latitude_default = 28.4
        tilt = _calculate_optimal_tilt(latitude_default)
        gain = _calculate_irradiation_gain(latitude_default, tilt)

        updated_results = []
        for item in sorted_results:
            lexical_density = getattr(item.chunk, "lexical_density", 0.5)
            confidence = _evaluate_confidence(item.relevance_score, lexical_density)
            updated_results.append(
                replace(
                    item,
                    suggested_tilt_angle=tilt,
                    confidence_level=confidence,
                    estimated_irradiation_gain=gain,
                )
            )

        return updated_results


def _calculate_optimal_tilt(latitude: float) -> float:
    """Calculate yearly average optimal tilt angle for solar panels."""
    return round(abs(latitude) * 0.76 + 3.1, 1)


def _calculate_irradiation_gain(latitude: float, tilt_angle: float) -> float:
    """Calculate approximate solar irradiation gain percentage based on tilt alignment."""
    lat_rad = math.radians(latitude)
    tilt_rad = math.radians(tilt_angle)
    cos_efficiency = math.cos(lat_rad - tilt_rad)
    gain_percentage = (cos_efficiency - math.cos(lat_rad)) * 100
    return round(max(0.0, gain_percentage), 1)


def _evaluate_confidence(relevance_score: float, lexical_density: float) -> str:
    if relevance_score >= 0.82 and lexical_density > 0.45:
        return "High (Highly Reliable)"
    elif relevance_score >= 0.60:
        return "Medium (Verify Context)"
    return "Low (Hallucination Risk)"


def extract_exact_terms(question: str) -> list[str]:
    if not FAULT_CONTEXT_RE.search(question):
        return []

    terms: set[str] = set()
    for match in FAULT_CODE_RE.finditer(question):
        raw = match.group(1).upper()
        if raw.isdigit():
            terms.add(raw)
            terms.add(raw.zfill(2))
            terms.add(f"F{raw.zfill(2)}")
            terms.add(f"Fault code {raw.zfill(2)}")
            terms.add(f"Error {raw.zfill(2)}")
        else:
            terms.add(raw)
            numeric = re.sub(r"\D", "", raw)
            if numeric:
                terms.add(numeric.zfill(2))
                terms.add(f"Fault code {numeric.zfill(2)}")

    for match in COMPACT_CODE_RE.finditer(question):
        raw = match.group(1).upper()
        terms.add(raw)
        numeric = re.sub(r"\D", "", raw)
        if numeric:
            terms.add(numeric.zfill(2))

    return sorted(terms)