"""Unit tests for chunking, retrieval, and citation verification."""

from datetime import UTC, datetime
from pathlib import Path

from app.core.config import Settings
from app.rag.chunker import chunk_loaded_texts
from app.rag.embeddings import HashEmbeddingProvider
from app.rag.retriever import Retriever, extract_exact_terms
from app.rag.types import DocumentChunk, LoadedText
from app.rag.vector_store import InMemoryVectorStore
from app.rag.verifier import validate_citations


def test_chunker_preserves_page_metadata_and_stable_ids(tmp_path):
    """Verify chunks keep page data and stable IDs."""
    chunks = chunk_loaded_texts(
        [LoadedText(text="Fault Codes\nFault code 07 overload timeout reduce load", page=4)],
        document_id="doc_123",
        filename="manual.txt",
        source_path=tmp_path / "manual.txt",
        upload_time=datetime.now(UTC).isoformat(),
        chunk_size=5,
        chunk_overlap=1,
    )
    assert chunks
    assert chunks[0].chunk_id == "doc_123_p4_c1"
    assert chunks[0].page == 4
    assert chunks[0].filename == "manual.txt"


def test_extract_exact_fault_code_terms():
    """Verify fault-code queries produce useful exact terms."""
    terms = extract_exact_terms("What does fault code 07 / F07 mean?")
    assert "07" in terms
    assert "F07" in terms
    assert "Fault code 07" in terms


def test_extract_exact_terms_messy_input():
    """Verify noisy user input still produces normalized exact-code terms."""
    messy_query = "   !!! alarm-code:  f--07??  or maybe error   08!!! "

    terms = extract_exact_terms(messy_query)

    assert "07" in terms
    assert "F07" in terms
    assert "08" in terms
    assert "Error 08" in terms


def test_extract_exact_terms_ignores_non_fault_questions():
    """Verify keyword fallback does not trigger for unrelated numeric questions."""
    assert extract_exact_terms("How many batteries are in this system? 12") == []


def test_in_memory_retriever_keyword_boosts_fault_codes(tmp_path):
    """Verify exact fault-code matches bypass weak semantics."""
    settings = Settings(
        data_dir=tmp_path / "data",
        vector_store_provider="memory",
        embedding_provider="hash",
        similarity_threshold=0.99,
    )
    embeddings = HashEmbeddingProvider()
    vector_store = InMemoryVectorStore()
    chunk = DocumentChunk(
        chunk_id="doc_a_p1_c1",
        document_id="doc_a",
        filename="manual.txt",
        page=1,
        section="Fault Codes",
        text="Fault code 07: Overload timeout. Reduce connected load.",
        source_path=str(Path("manual.txt")),
        upload_time=datetime.now(UTC).isoformat(),
    )
    vector_store.add_chunks([chunk], embeddings.embed_documents([chunk.text]))

    retriever = Retriever(settings=settings, embeddings=embeddings, vector_store=vector_store)
    results = retriever.retrieve("How do I fix F07?", top_k=3)
    assert results
    assert results[0].chunk.chunk_id == "doc_a_p1_c1"
    assert results[0].source == "keyword"


def test_validate_citations_removes_invented_source_ids():
    """Verify fake citation IDs are removed."""
    answer, warnings = validate_citations("Use this step [Source 1] and this [Source 9].", 1)
    assert "[Source 1]" in answer
    assert "[Source 9]" not in answer
    assert warnings == ["Removed unsupported citation [Source 9]."]
