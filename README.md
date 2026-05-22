# Trustworthy Domain-Specific RAG Chatbot With Provenance

A document-grounded Retrieval-Augmented Generation (RAG) chatbot for technical support teams working with solar and energy equipment manuals.

The system lets users upload technical documents, ask engineering support questions, retrieve the most relevant passages, generate grounded answers, and inspect the exact source evidence behind each response.

This version uses a **FastAPI backend** and a simpler **Streamlit frontend** so a beginner-friendly student team can build, test, demo, and extend the project without the learning curve of React.

## Table Of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Local Setup With uv](#local-setup-with-uv)
- [Running The App](#running-the-app)
- [API Reference](#api-reference)
- [How The RAG Pipeline Works](#how-the-rag-pipeline-works)
- [Grounding And Provenance](#grounding-and-provenance)
- [Hallucination Controls](#hallucination-controls)
- [Fault-Code Exact Lookup](#fault-code-exact-lookup)
- [Local Response Caching](#local-response-caching)
- [Testing And Quality Checks](#testing-and-quality-checks)
- [Docker Usage](#docker-usage)
- [Demo Flow](#demo-flow)
- [Team Workflow](#team-workflow)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)
- [Troubleshooting](#troubleshooting)

## Project Overview

Engineers and field technicians often need to search large inverter, battery, PV module, fan, charge controller, and maintenance manuals to find fault codes, alarm meanings, troubleshooting steps, and safety instructions.

This project provides a trustworthy technical-support assistant that can:

- Upload and index technical manuals.
- Retrieve relevant document passages.
- Answer questions using retrieved evidence.
- Show citations and source cards.
- Refuse unsupported answers in document mode.
- Preserve document provenance such as filename, page, section, chunk ID, relevance score, and supporting text.
- Provide a fast exact fault-code lookup that does not call the LLM.

The goal is not just to "chat with a PDF". The goal is to build a transparent document QA system that can be extended toward real-world technical support.

## Problem Statement

Traditional manual search is slow and error-prone. Engineers may spend significant time looking for a fault code across large manufacturer PDFs or maintenance documents.

A normal LLM chatbot can sound confident even when it is wrong. For technical support, that is risky. This project reduces that risk by grounding answers in uploaded documents and exposing the evidence used to answer.

When the indexed documents do not contain enough information, the assistant should say:

```text
I could not find enough information in the uploaded documents to answer this reliably.
```

## Key Features

- Streamlit web UI for document upload, chat, source cards, and fault-code lookup.
- FastAPI backend with modular RAG pipeline.
- uv-managed Python projects for both backend and frontend.
- Upload support for PDF, DOCX, TXT, Markdown, and MD files.
- PDF page-number preservation where text extraction supports it.
- Text cleaning and chunking with overlap.
- Persistent vector database using ChromaDB by default.
- Configurable embeddings.
- OpenAI-compatible LLM provider support.
- Mock generator and hash embeddings for local tests.
- Document mode, general mode, and hybrid mode.
- Default `ALLOW_GENERAL_KNOWLEDGE=false` for safer document-grounded behavior.
- Citation validation.
- Exact fault-code lookup endpoint and table view.
- Local response cache to reduce repeated LLM API calls.
- Backend tests with pytest.
- Ruff linting and formatting.
- Optional Docker support.

## Technology Stack

### Backend

- Python 3.11+
- uv for dependency management and execution
- FastAPI
- Uvicorn
- Pydantic
- python-dotenv / pydantic-settings
- ChromaDB
- SentenceTransformers or hash/mock embeddings
- pypdf
- python-docx
- Markdown document support
- pytest
- ruff

### Frontend

- Python
- Streamlit
- httpx
- uv

### Optional

- Docker
- Docker Compose
- Groq, OpenAI, or another OpenAI-compatible LLM provider

## Architecture

```text
User
  |
  v
Streamlit Frontend
  |  Upload documents
  |  Ask questions
  |  Lookup fault codes
  v
FastAPI Backend
  |
  +-- Upload API
  |     +-- Validate file type and size
  |     +-- Save uploaded document safely
  |     +-- Extract text
  |     +-- Clean text
  |     +-- Chunk text
  |     +-- Embed chunks
  |     +-- Store vectors and metadata
  |
  +-- Chat API
  |     +-- Retrieve relevant chunks
  |     +-- Apply similarity threshold
  |     +-- Build grounded prompt
  |     +-- Generate answer
  |     +-- Validate citations
  |     +-- Return answer and provenance
  |
  +-- Fault-Code Lookup API
        +-- Normalize code variants
        +-- Search exact terms in indexed chunks
        +-- Return matching table rows without LLM call

Persistent Storage
  |
  +-- data/raw              Uploaded files
  +-- data/processed        Document registry and response cache
  +-- data/vector_store     ChromaDB vector store
```

## Project Structure

```text
rag-chatbot-streamlit/
|
+-- README.md                         Main project documentation.
+-- .env.example                      Example environment variables with no real secrets.
+-- .gitignore                        Files and folders Git should ignore.
+-- docker-compose.yml                Optional Docker Compose setup.
+-- project_structure.txt             Human-readable project structure notes.
|
+-- backend/                          FastAPI backend and RAG pipeline.
|   +-- pyproject.toml                 uv project and backend dependencies.
|   +-- uv.lock                        Locked backend dependency versions.
|   +-- Dockerfile                     Optional backend Docker image.
|   +-- README.md                      Backend-specific notes.
|   +-- app/
|   |   +-- main.py                    FastAPI app factory and route registration.
|   |   +-- api/
|   |   |   +-- chat.py                POST /chat endpoint.
|   |   |   +-- documents.py           GET /documents endpoint.
|   |   |   +-- fault_codes.py         POST /fault-codes/lookup endpoint.
|   |   |   +-- upload.py              POST /documents/upload endpoint.
|   |   +-- core/
|   |   |   +-- config.py              Environment-backed settings.
|   |   |   +-- dependencies.py        Shared RAG service dependency.
|   |   |   +-- logging.py             Logging configuration.
|   |   +-- models/
|   |   |   +-- schemas.py             Pydantic request and response models.
|   |   +-- rag/
|   |   |   +-- chunker.py             Converts extracted text into metadata-rich chunks.
|   |   |   +-- embeddings.py          Embedding provider implementations.
|   |   |   +-- generator.py           LLM and mock generation providers.
|   |   |   +-- loader.py              PDF, DOCX, TXT, and Markdown text loading.
|   |   |   +-- prompt_builder.py      Grounded and general prompt builders.
|   |   |   +-- provenance.py          SourceReference construction.
|   |   |   +-- registry.py            Indexed document registry.
|   |   |   +-- response_cache.py      SQLite response cache.
|   |   |   +-- retriever.py           Semantic retrieval and exact-code term extraction.
|   |   |   +-- service.py             Main orchestration layer.
|   |   |   +-- types.py               Internal dataclasses.
|   |   |   +-- vector_store.py        ChromaDB and in-memory vector store.
|   |   |   +-- verifier.py            Refusal text and citation validation.
|   |   +-- utils/
|   |       +-- text_cleaning.py       Text normalization and snippets.
|   +-- data/
|   |   +-- raw/                       Uploaded files, created at runtime.
|   |   +-- processed/                 Registry and cache files, created at runtime.
|   |   +-- vector_store/              Persistent ChromaDB files, created at runtime.
|   +-- tests/
|       +-- conftest.py                Test app fixture and test settings.
|       +-- test_api.py                API tests.
|       +-- test_rag_units.py          RAG unit tests.
|
+-- frontend/                         Streamlit frontend.
|   +-- pyproject.toml                 uv project and frontend dependencies.
|   +-- uv.lock                        Locked frontend dependency versions.
|   +-- Dockerfile                     Optional frontend Docker image.
|   +-- README.md                      Frontend-specific notes.
|   +-- app.py                         Streamlit UI.
|   +-- app_orig.py                    Backup of a previous UI version.
|   +-- .streamlit/
|       +-- config.toml                Streamlit theme/server config.
|
+-- docs/
    +-- acceptance_criteria.md         Completion checklist.
    +-- architecture.md                Architecture notes.
    +-- demo_flow.md                   Suggested demo script.
    +-- evaluation.md                  Evaluation plan and question types.
    +-- slack_tracker.md               Slack project tracker template.
    +-- team_plan.md                   Three-person team work plan.
```

## Prerequisites

Install the following:

- Python 3.11 or newer
- uv
- Git
- Optional: Docker and Docker Compose
- Optional: an LLM API key, such as Groq or OpenAI-compatible provider

Check uv:

```bash
uv --version
```

If uv is not installed, follow the official uv installation guide:

```text
https://docs.astral.sh/uv/
```

## Environment Variables

Copy the example file:

```bash
cp .env.example .env
cp .env.example backend/.env
```

Important settings:

```env
LLM_PROVIDER=mock
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
LLM_API_BASE=https://api.openai.com/v1

EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

VECTOR_STORE_PROVIDER=chroma
VECTOR_STORE_PATH=
VECTOR_COLLECTION_NAME=technical_manual_chunks

CHUNK_SIZE=750
CHUNK_OVERLAP=150
TOP_K=5
SIMILARITY_THRESHOLD=0.35

ALLOW_GENERAL_KNOWLEDGE=false

RESPONSE_CACHE_ENABLED=true
RESPONSE_CACHE_TTL_SECONDS=604800

MAX_UPLOAD_SIZE_MB=25
ALLOWED_FILE_TYPES=.pdf,.docx,.txt,.md,.markdown
```

For a Groq-style OpenAI-compatible setup, configure:

```env
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key_here
LLM_API_BASE=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-8b-instant
```

Never commit real API keys.

## Local Setup With uv

### Backend

```bash
cd backend
uv sync
```

### Frontend

```bash
cd frontend
uv sync
```

This project intentionally uses uv instead of `python -m venv`, `pip install`, or plain `python script.py` workflows.

## Running The App

Start the backend in one terminal:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Check that the backend is alive:

```bash
curl http://localhost:8000/energy
```

Expected response:

```json
{
  "status": "ok"
}
```

Start the frontend in a second terminal:

```bash
cd frontend
uv run streamlit run app.py
```

Open the Streamlit UI:

```text
http://localhost:8501
```

The frontend expects the backend at:

```text
http://localhost:8000
```

You can change this in the sidebar using the Backend URL input.

## API Reference

### GET /energy

Health/status endpoint.

```bash
curl http://localhost:8000/energy
```

Response:

```json
{
  "status": "ok"
}
```

### POST /documents/upload

Uploads and indexes a document.

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@sample_manual.pdf"
```

Example response:

```json
{
  "document_id": "doc_123",
  "filename": "sample_manual.pdf",
  "chunks_created": 42,
  "status": "indexed"
}
```

### GET /documents

Lists indexed documents.

```bash
curl http://localhost:8000/documents
```

Example response:

```json
[
  {
    "document_id": "doc_123",
    "filename": "sample_manual.pdf",
    "upload_time": "2026-05-22T10:00:00+00:00",
    "chunks_created": 42,
    "status": "indexed",
    "source_path": "data/raw/doc_123_sample_manual.pdf"
  }
]
```

### POST /chat

Asks a grounded question.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What does fault code 07 mean?",
    "top_k": 5,
    "mode": "document"
  }'
```

Example grounded response:

```json
{
  "answer": "Fault code 07 indicates overload timeout and the manual recommends reducing the connected load before restarting the inverter [Source 1].",
  "grounded": true,
  "confidence": "high",
  "mode": "document",
  "sources": [
    {
      "source_id": "Source 1",
      "document_id": "doc_123",
      "filename": "voltronic_manual.pdf",
      "page": 34,
      "section": "Fault Codes",
      "chunk_id": "doc_123_page_34_chunk_2",
      "relevance_score": 0.87,
      "text_snippet": "Fault code 07: Overload timeout...",
      "full_text": "Fault code 07: Overload timeout. Recommended action..."
    }
  ],
  "warnings": [
    "For high-risk electrical work, follow manufacturer safety instructions and qualified technician procedures."
  ]
}
```

Example refusal response:

```json
{
  "answer": "I could not find enough information in the uploaded documents to answer this reliably.",
  "grounded": false,
  "confidence": "low",
  "mode": "document",
  "sources": [],
  "warnings": [
    "No retrieved chunk passed the relevance threshold."
  ]
}
```

### POST /fault-codes/lookup

Performs exact fault-code matching without an LLM call.

```bash
curl -X POST http://localhost:8000/fault-codes/lookup \
  -H "Content-Type: application/json" \
  -d '{
    "code": "07",
    "top_k": 10
  }'
```

Example response:

```json
{
  "code": "07",
  "normalized_terms": [
    "Fault code 07",
    "Error code 07",
    "Alarm code 07",
    "F07",
    "07"
  ],
  "matches": [
    {
      "source_id": "Match 1",
      "document_id": "doc_123",
      "filename": "voltronic_manual.txt",
      "page": null,
      "section": "Fault Codes",
      "chunk_id": "doc_123_page_0_chunk_1",
      "relevance_score": 0.97,
      "matched_terms": [
        "Fault code 07",
        "07"
      ],
      "text_snippet": "Fault code 07: Overload timeout...",
      "full_text": "Fault code 07: Overload timeout. Recommended action..."
    }
  ],
  "warnings": []
}
```

## How The RAG Pipeline Works

1. A user uploads a supported technical document.
2. The backend validates the file type and size.
3. The file is saved under `backend/data/raw/`.
4. The loader extracts text:
   - PDF pages are extracted with page metadata.
   - DOCX files are read paragraph by paragraph.
   - TXT, MD, and Markdown files are read as text documents.
5. Text is cleaned to remove extra whitespace and formatting noise.
6. Text is split into overlapping chunks.
7. Each chunk receives metadata:
   - document ID
   - filename
   - page number where available
   - section heading where detected
   - chunk ID
   - source path
   - upload time
8. Chunks are embedded.
9. Chunks and metadata are stored in ChromaDB.
10. At question time, the retriever finds relevant chunks.
11. The prompt builder creates a strict grounded prompt.
12. The generator produces an answer.
13. The verifier checks citation integrity.
14. The API returns the answer plus structured provenance.

## Grounding And Provenance

Every factual document-mode answer should be supported by retrieved sources.

The backend returns:

- `answer`
- `grounded`
- `confidence`
- `mode`
- `sources`
- `warnings`

Each source includes:

- source ID
- document ID
- filename
- page number if available
- section if available
- chunk ID
- relevance score
- snippet
- full chunk text

The frontend displays this information as evidence cards and expandable source details so users can verify the answer.

## Hallucination Controls

The system includes several safeguards:

- Document mode is the default.
- General knowledge is disabled by default through `ALLOW_GENERAL_KNOWLEDGE=false`.
- If retrieval returns no strong evidence, the assistant refuses.
- Retrieved chunks are filtered using a similarity threshold.
- The prompt instructs the LLM to answer only from provided context.
- Citation validation removes unsupported source markers.
- Source metadata is taken from the indexed document store, not invented by the LLM.
- Safety warnings are included for high-risk electrical work.
- Exact fault-code lookup can be used before generation.

## Fault-Code Exact Lookup

Technical manuals often use precise labels such as:

- `07`
- `F07`
- `Fault code 07`
- `Error 07`
- `Alarm 07`

Semantic retrieval can miss exact labels, especially short codes. The app includes a dedicated exact lookup flow:

- The user enters a fault code in the Streamlit panel.
- The backend normalizes common variants.
- The vector store performs keyword matching against indexed chunks.
- Matching rows are returned without calling the LLM.
- The UI shows a table with file, page, section, chunk ID, score, matched terms, and snippet.

This is useful for quick verification and for saving LLM API usage.

## Local Response Caching

Repeated chat questions can consume unnecessary LLM calls. The backend includes a local SQLite response cache.

Cache settings:

```env
RESPONSE_CACHE_ENABLED=true
RESPONSE_CACHE_TTL_SECONDS=604800
```

The cache key includes:

- normalized question
- answer mode
- top_k
- indexed document fingerprint
- LLM settings
- embedding settings
- similarity threshold
- general knowledge setting

This means cached responses are automatically invalidated when the indexed document set or key settings change.

The cache is stored under:

```text
backend/data/processed/response_cache.sqlite3
```

When a response comes from cache, the backend adds a warning:

```text
Returned from local response cache; no LLM API call was made.
```

## Testing And Quality Checks

Run backend tests:

```bash
cd backend
uv run pytest
```

Run linting:

```bash
cd backend
uv run ruff check .
```

Check formatting:

```bash
cd backend
uv run ruff format --check .
```

Apply formatting:

```bash
cd backend
uv run ruff format .
```

Check Streamlit syntax:

```bash
cd frontend
uv run python -m py_compile app.py
```

Current backend test coverage includes:

- status endpoint
- document upload
- unsupported file type handling
- empty document handling
- corrupted PDF handling
- document listing
- chat response format
- refusal behavior when no documents are indexed
- general knowledge disabled behavior
- exact fault-code lookup
- RAG unit tests

## Docker Usage

Docker is optional. Local development should use uv directly.

Run both services with Docker Compose:

```bash
docker compose up --build
```

Backend:

```text
http://localhost:8000
```

Frontend:

```text
http://localhost:8501
```

Use Docker when:

- teammates want a similar runtime environment
- you want easier demo setup
- you want to avoid local dependency mismatch
- you are preparing for deployment experiments

Use direct uv commands when:

- actively developing code
- running tests
- debugging backend modules
- iterating on the Streamlit app

## Demo Flow

Suggested demo:

1. Start the backend:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

2. Start the frontend:

```bash
cd frontend
uv run streamlit run app.py
```

3. Open the Streamlit app.
4. Upload a technical manual.
5. Show that the document appears in the indexed document list.
6. Use the fault-code exact lookup panel for a known code such as `07` or `F07`.
7. Ask a chat question:

```text
What does fault code 07 mean and how should it be fixed?
```

8. Show the grounded answer and source cards.
9. Expand the evidence chunk.
10. Ask an unsupported question:

```text
What is the Wi-Fi password for this inverter?
```

11. Show that the assistant refuses instead of guessing.
12. Explain retrieval, citations, provenance, caching, and safety controls.

## Team Workflow

Recommended roles for a three-person team:

### Backend/API Lead

- Own FastAPI endpoints.
- Maintain upload validation.
- Improve API error handling.
- Add backend tests.
- Review environment and Docker setup.

### RAG/AI Pipeline Lead

- Improve document loading.
- Improve chunking and metadata preservation.
- Tune embeddings and retrieval thresholds.
- Improve prompt quality.
- Expand exact fault-code support.
- Evaluate answer quality and citation accuracy.

### Frontend/Evaluation Lead

- Own Streamlit UI.
- Improve source card design.
- Prepare demo documents.
- Build evaluation question sets.
- Record test outcomes.
- Support final presentation.

### GitHub Workflow

Use branches:

- `main`
- `dev`
- `backend`
- `rag-pipeline`
- `frontend`
- `docs`

Recommended flow:

1. Create or pick a GitHub issue.
2. Create a branch from `dev`.
3. Make focused changes.
4. Run tests and checks.
5. Commit with a clear message.
6. Push the branch.
7. Open a pull request into `dev`.
8. Ask at least one teammate to review.
9. Merge after tests pass.
10. Periodically merge `dev` into `main` for stable demo versions.

Suggested PR checklist:

```text
- What changed?
- Why was it needed?
- How was it tested?
- Any known limitations?
- Screenshots if UI changed?
```

## Limitations

- OCR for scanned PDFs is not implemented.
- Table extraction from complex manuals may be imperfect.
- PDF text extraction quality depends on the PDF.
- Exact fault-code lookup is keyword-based and may need domain-specific tuning.
- LLM quality depends on the configured provider and model.
- The project is built for local/demo use, not production multi-user deployment yet.
- Authentication and role-based access control are not implemented.

## Future Improvements

- OCR support for scanned manuals.
- Better table extraction.
- Advanced section heading detection.
- Metadata filters by document, equipment type, manufacturer, or model.
- Evaluation dashboard.
- Admin page for clearing indexed documents.
- User accounts and access control.
- Conversation history persistence.
- Hybrid RAG plus structured analytics over CSV or time-series datasets.
- Deployment to a cloud platform.
- Human feedback collection for answer quality.

## Troubleshooting

### Backend cannot start

Run:

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Check `.env` values and confirm port `8000` is free.

### Frontend cannot connect to backend

Make sure the backend is running:

```bash
curl http://localhost:8000/energy
```

In the Streamlit sidebar, confirm Backend URL is:

```text
http://localhost:8000
```

### Upload fails

Check:

- file extension is allowed
- file is not empty
- file size is below `MAX_UPLOAD_SIZE_MB`
- backend logs for extraction errors

### Chat refuses too often

Try:

- upload a more relevant manual
- increase `TOP_K`
- lower `SIMILARITY_THRESHOLD` carefully
- ask a more specific question
- use exact fault-code lookup for short codes

### Groq or OpenAI-compatible calls fail

Check:

- `LLM_PROVIDER=openai`
- `LLM_API_KEY` is set
- `LLM_API_BASE` is correct
- `LLM_MODEL` exists for that provider
- rate limits have not been exceeded

### Reset all local indexed data

Stop the backend and frontend first.

Then remove runtime data:

```bash
cd backend
rm -rf data/raw data/processed data/vector_store
```

Restart the backend and upload documents again.

## Acceptance Criteria

The MVP is successful when:

- A user can upload a technical manual.
- The backend extracts and chunks the document.
- Chunks are embedded and stored in the vector database.
- The Streamlit UI can ask questions.
- The backend retrieves relevant chunks.
- The generated answer uses retrieved evidence.
- Citations and source cards are shown.
- Unsupported questions are refused in document mode.
- Exact fault-code lookup returns matching chunks without an LLM call.
- Tests pass with `uv run pytest`.
- The app can be started with documented uv commands.

## License

No license file is currently included. Add a license before publishing the repository publicly if you want others to reuse or modify the code.
