# Architecture

The MVP is a document-grounded RAG application with a clear split between UI, API, retrieval, and generation.

```text
User
  -> React UI
  -> FastAPI
  -> Document Loader
  -> Cleaner
  -> Chunker
  -> Embedding Provider
  -> ChromaDB
  -> Retriever
  -> Prompt Builder
  -> LLM Generator
  -> Citation Verifier
  -> Provenance Response
```

## Backend Modules

- `api/`: HTTP routes for uploads, document listing, and chat.
- `rag/loader.py`: PDF, DOCX, TXT, and Markdown extraction.
- `rag/chunker.py`: page-aware chunk creation with stable IDs.
- `rag/embeddings.py`: SentenceTransformers, OpenAI-compatible, and hash providers.
- `rag/vector_store.py`: ChromaDB persistence plus in-memory test store.
- `rag/retriever.py`: semantic retrieval and exact fault-code matching.
- `rag/generator.py`: OpenAI-compatible generation and mock fallback.
- `rag/verifier.py`: citation validation and refusal detection.
- `rag/provenance.py`: structured source references for the UI.

## Data Flow

1. Uploads are validated by extension and size.
2. Files are stored in `backend/data/raw`.
3. Extracted text is cleaned and chunked.
4. Chunk embeddings and metadata are persisted in ChromaDB.
5. User questions are embedded and retrieved.
6. Weak retrieval results trigger refusal in document mode.
7. Strong results are formatted into a strict grounded prompt.
8. Answers are citation-checked before returning to the UI.
