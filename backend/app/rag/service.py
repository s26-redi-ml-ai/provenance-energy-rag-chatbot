"""Main RAG orchestration service used by the API layer."""

import re
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import Settings
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ConfidenceLevel,
    DocumentMetadata,
    FaultCodeLookupRequest,
    FaultCodeLookupResponse,
    FaultCodeMatch,
    UploadResponse,
)
from app.rag.chunker import chunk_loaded_texts
from app.rag.embeddings import create_embedding_provider
from app.rag.generator import GenerationError, create_generator
from app.rag.loader import DocumentLoadingError, load_document
from app.rag.prompt_builder import build_general_prompt, build_grounded_prompt
from app.rag.provenance import build_source_references
from app.rag.registry import DocumentRegistry
from app.rag.response_cache import ResponseCache, build_cache_key, document_fingerprint
from app.rag.retriever import Retriever, extract_exact_terms
from app.rag.vector_store import create_vector_store
from app.rag.verifier import REFUSAL, is_refusal, validate_citations
from app.utils.text_cleaning import make_snippet


class RAGService:
    """Coordinate uploads, retrieval, generation, provenance, and response caching."""

    def __init__(self, settings: Settings) -> None:
        """Create the providers and persistent registries used by the RAG workflow."""
        self.settings = settings
        self.settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.settings.resolved_vector_store_path.mkdir(parents=True, exist_ok=True)

        self.embeddings = create_embedding_provider(settings)
        self.vector_store = create_vector_store(settings)
        self.retriever = Retriever(
            settings=settings,
            embeddings=self.embeddings,
            vector_store=self.vector_store,
        )
        self.generator = create_generator(settings)
        self.registry = DocumentRegistry(settings.processed_data_dir)
        self.response_cache = (
            ResponseCache(
                settings.processed_data_dir / "response_cache.sqlite3",
                ttl_seconds=settings.response_cache_ttl_seconds,
            )
            if settings.response_cache_enabled
            else None
        )

    def index_file(self, *, document_id: str, filename: str, path: Path) -> UploadResponse:
        """Extract, chunk, embed, store, and register one uploaded document."""
        # Convert the uploaded file into loaded text blocks before chunking.
        loaded = load_document(path, filename)
        upload_time = datetime.now(UTC).isoformat()
        chunks = chunk_loaded_texts(
            loaded,
            document_id=document_id,
            filename=filename,
            source_path=path,
            upload_time=upload_time,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        if not chunks:
            raise DocumentLoadingError("No chunks could be created from the uploaded document.")

        # Embeddings make each chunk searchable by meaning in the vector store.
        embeddings = self.embeddings.embed_documents([chunk.text for chunk in chunks])
        self.vector_store.add_chunks(chunks, embeddings)
        self.registry.upsert(
            DocumentMetadata(
                document_id=document_id,
                filename=filename,
                upload_time=upload_time,
                chunks_created=len(chunks),
                status="indexed",
                source_path=str(path),
            )
        )
        return UploadResponse(
            document_id=document_id,
            filename=filename,
            chunks_created=len(chunks),
            status="indexed",
        )

    def list_documents(self) -> list[DocumentMetadata]:
        """Return document metadata from the local registry for the UI and API."""
        return self.registry.list_documents()

    def lookup_fault_code(self, request: FaultCodeLookupRequest) -> FaultCodeLookupResponse:
        """Find exact fault-code matches across indexed chunks for lookup-table display."""
        normalized_terms = _fault_lookup_terms(request.code)
        warnings: list[str] = []
        if not normalized_terms:
            return FaultCodeLookupResponse(
                code=request.code,
                normalized_terms=[],
                matches=[],
                warnings=["No fault-code-like term could be normalized from the request."],
            )

        retrieval_limit = max(request.top_k * 5, request.top_k)
        retrieved = self.vector_store.keyword_search(normalized_terms, top_k=retrieval_limit)

        matches: list[FaultCodeMatch] = []
        seen_chunk_ids: set[str] = set()
        for item in retrieved:
            if item.chunk.chunk_id in seen_chunk_ids:
                continue

            matched_terms = _matched_fault_terms(item.chunk.text, normalized_terms)
            if not matched_terms:
                continue

            seen_chunk_ids.add(item.chunk.chunk_id)
            matches.append(
                FaultCodeMatch(
                    source_id=f"Match {len(matches) + 1}",
                    document_id=item.chunk.document_id,
                    filename=item.chunk.filename,
                    page=item.chunk.page,
                    section=item.chunk.section,
                    chunk_id=item.chunk.chunk_id,
                    relevance_score=round(
                        max(item.relevance_score, _fault_lookup_score(matched_terms)),
                        4,
                    ),
                    matched_terms=matched_terms,
                    text_snippet=make_snippet(item.chunk.text),
                    full_text=item.chunk.text,
                )
            )
            if len(matches) >= request.top_k:
                break

        if not matches:
            warnings.append("No indexed chunk contained an exact matching fault-code term.")

        return FaultCodeLookupResponse(
            code=request.code,
            normalized_terms=normalized_terms,
            matches=matches,
            warnings=warnings,
        )

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Answer a user question using document retrieval, generation, and guardrails."""
        # Cache first so repeated questions do not waste LLM API calls.
        cache_key = self._response_cache_key(request)
        cached_response = self._get_cached_response(cache_key)
        if cached_response is not None:
            return cached_response

        if request.mode == "general":
            response = self._general_answer(request)
            self._cache_response(cache_key, response)
            return response

        # Document and hybrid modes must retrieve evidence before answering.
        retrieved = self.retriever.retrieve(request.question, request.top_k)
        if not retrieved:
            if request.mode == "hybrid" and self.settings.allow_general_knowledge:
                response = self._general_answer(
                    request,
                    warnings=["No retrieved chunk passed the relevance threshold."],
                )
                self._cache_response(cache_key, response)
                return response

            response = ChatResponse(
                answer=REFUSAL,
                grounded=False,
                confidence="low",
                mode=request.mode,
                sources=[],
                warnings=["No retrieved chunk passed the relevance threshold."],
            )
            self._cache_response(cache_key, response)
            return response

        sources = build_source_references(retrieved)
        prompt = build_grounded_prompt(request.question, retrieved)
        try:
            answer = self.generator.generate(prompt)
        except GenerationError as exc:
            return ChatResponse(
                answer=REFUSAL,
                grounded=False,
                confidence="low",
                mode=request.mode,
                sources=sources,
                warnings=[str(exc)],
            )

        answer, citation_warnings = validate_citations(answer, len(sources))
        grounded = not is_refusal(answer)
        warnings = citation_warnings
        if grounded:
            warnings.append(
                "For high-risk electrical work, follow manufacturer safety instructions "
                "and qualified technician procedures."
            )

        response = ChatResponse(
            answer=answer,
            grounded=grounded,
            confidence=_confidence_from_sources(retrieved),
            mode=request.mode,
            sources=sources if grounded else [],
            warnings=warnings,
        )
        self._cache_response(cache_key, response)
        return response

    def _general_answer(
        self,
        request: ChatRequest,
        warnings: list[str] | None = None,
    ) -> ChatResponse:
        """Generate a clearly labeled non-grounded answer when the mode permits it."""
        warnings = list(warnings or [])
        if not self.settings.allow_general_knowledge:
            return ChatResponse(
                answer=(
                    "General knowledge mode is disabled. Ask in document mode or enable "
                    "ALLOW_GENERAL_KNOWLEDGE=true."
                ),
                grounded=False,
                confidence="low",
                mode=request.mode,
                sources=[],
                warnings=["ALLOW_GENERAL_KNOWLEDGE is false."],
            )

        prompt = build_general_prompt(request.question, request.mode)
        try:
            answer = self.generator.generate(prompt)
        except GenerationError as exc:
            answer = "General knowledge answer could not be generated."
            warnings.append(str(exc))
        warnings.append(
            "This answer is based on general knowledge and not directly on the uploaded documents."
        )
        return ChatResponse(
            answer=answer,
            grounded=False,
            confidence="low",
            mode=request.mode,
            sources=[],
            warnings=warnings,
        )

    def _response_cache_key(self, request: ChatRequest) -> str:
        """Build a cache key that changes when documents or core settings change."""
        documents = self.registry.list_documents()
        settings_fingerprint = {
            "llm_provider": self.settings.llm_provider,
            "llm_model": self.settings.llm_model,
            "embedding_provider": self.settings.embedding_provider,
            "embedding_model": self.settings.embedding_model,
            "similarity_threshold": self.settings.similarity_threshold,
            "allow_general_knowledge": self.settings.allow_general_knowledge,
        }
        return build_cache_key(
            request=request,
            document_fingerprint_value=document_fingerprint(documents),
            settings_fingerprint=settings_fingerprint,
        )

    def _get_cached_response(self, cache_key: str) -> ChatResponse | None:
        """Return a cached chat response and annotate it for transparency."""
        if self.response_cache is None:
            return None

        response = self.response_cache.get(cache_key)
        if response is None:
            return None

        response.warnings = [
            *response.warnings,
            "Returned from local response cache; no LLM API call was made.",
        ]
        return response

    def _cache_response(self, cache_key: str, response: ChatResponse) -> None:
        """Persist a chat response when local response caching is enabled."""
        if self.response_cache is not None:
            self.response_cache.set(cache_key, response)


def _fault_lookup_terms(code: str) -> list[str]:
    """Expand one fault-code query into equivalent searchable forms."""
    cleaned = " ".join(code.strip().upper().split())
    if not cleaned:
        return []

    terms: set[str] = set(extract_exact_terms(f"fault code {cleaned}"))
    terms.add(cleaned)

    compact = re.sub(r"[^A-Z0-9]", "", cleaned)
    if compact:
        terms.add(compact)

    numeric = re.sub(r"\D", "", compact or cleaned)
    prefix = re.sub(r"\d", "", compact)
    if numeric:
        padded = numeric.zfill(2) if len(numeric) < 2 else numeric
        terms.update(
            {
                numeric,
                padded,
                f"F{padded}",
                f"E{padded}",
                f"Fault {padded}",
                f"Fault code {padded}",
                f"Error {padded}",
                f"Error code {padded}",
                f"Alarm {padded}",
                f"Alarm code {padded}",
                f"Warning {padded}",
                f"Warning code {padded}",
            }
        )
        if prefix:
            terms.add(f"{prefix}{padded}")

    return sorted(terms, key=lambda term: (-len(term), term))


def _matched_fault_terms(text: str, terms: list[str]) -> list[str]:
    """Return normalized lookup terms that occur as exact terms in a chunk."""
    matches: list[str] = []
    for term in terms:
        pattern = re.compile(
            rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])",
            re.IGNORECASE,
        )
        if pattern.search(text):
            matches.append(term)
    return matches


def _fault_lookup_score(matched_terms: list[str]) -> float:
    """Score exact fault-code matches higher when descriptive terms are present."""
    has_descriptive_term = any(
        keyword in term.lower()
        for term in matched_terms
        for keyword in ("fault", "error", "alarm", "warning")
    )
    score = 0.93 + min(len(matched_terms), 4) * 0.01
    if has_descriptive_term:
        score += 0.03
    return min(1.0, score)


def _confidence_from_sources(retrieved: list) -> ConfidenceLevel:
    """Map retrieval strength into the low/medium/high confidence label."""
    if not retrieved:
        return "low"
    best = retrieved[0].relevance_score
    if best >= 0.78 and len(retrieved) >= 2:
        return "high"
    if best >= 0.55:
        return "medium"
    return "low"
