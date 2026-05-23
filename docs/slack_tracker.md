# Slack Project Tracker Message

Project: Trustworthy Domain-Specific RAG Chatbot with Provenance

Goal: Build a UI-based technical-support chatbot that answers from uploaded solar and energy equipment manuals, shows source evidence, and refuses unsupported answers.

Current stage: TODO / Week 1 setup.

Team roles:

- Backend/API Lead: FastAPI, uv setup, endpoints, validation, tests.
- RAG/AI Lead: extraction, chunking, embeddings, ChromaDB, retrieval, prompts, provenance.
- Frontend/Evaluation Lead: React UI, source cards, evaluation questions, demo flow.

Main workstreams:

- TODO Backend API
- TODO RAG pipeline
- TODO Frontend UI
- TODO Evaluation and demo
- TODO Documentation

Weekly milestones:

- Week 1: repo, setup, sample documents, API contracts.
- Week 2: ingestion, chunking, embeddings, vector search.
- Week 3: backend integration and grounded chat.
- Week 4: frontend and provenance UI.
- Week 5: testing, evaluation, docs, demo.

Update format:

```text
Yesterday/Last Update:
What I worked on.

Today/Next:
What I will work on next.

Blockers:
Anything preventing progress.

Link/PR/Files:
GitHub issue, pull request, document, or screenshot if available.
```

Definition of Done:

- Upload works for supported document types.
- Chat returns grounded answers with citations.
- Unsupported questions trigger refusal.
- Source cards show filename, page, chunk ID, score, and evidence.
- Tests run with `uv run pytest`.
- Demo flow is ready.
