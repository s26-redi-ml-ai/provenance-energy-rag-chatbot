# Backend

FastAPI backend for the Trustworthy Domain-Specific RAG Chatbot with Provenance.

## Setup

```bash
cd backend
uv sync
```

Copy the root `.env.example` to `backend/.env` or export the variables in your shell.

## Run

```bash
uv run uvicorn app.main:app --reload
```

API status:

```bash
curl http://localhost:8000/energy
```

## Test

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

## Key Settings

- `LLM_PROVIDER=mock` works without API keys for offline demos and tests.
- `LLM_PROVIDER=openai` uses an OpenAI-compatible `/chat/completions` endpoint.
- `EMBEDDING_PROVIDER=sentence-transformers` is the default local embedding path.
- `EMBEDDING_PROVIDER=hash` is deterministic and useful for tests.
- `ALLOW_GENERAL_KNOWLEDGE=false` keeps the chatbot document-grounded by default.

## API Examples

Upload a manual:

```bash
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@manual.pdf"
```

Ask a document-grounded question:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What does fault code 07 mean?","top_k":5,"mode":"document"}'
```
