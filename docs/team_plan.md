# Team Plan

## Team Member 1: Backend and API Lead

- Own FastAPI setup and uv workflow.
- Build `/energy`, `/documents/upload`, `/documents`, and `/chat`.
- Handle validation, errors, logging, and tests.
- Keep API contracts stable for the frontend.

## Team Member 2: RAG and AI Pipeline Lead

- Own loaders, cleaning, chunking, embeddings, ChromaDB, and retrieval.
- Tune similarity threshold and chunk settings.
- Implement exact fault-code matching.
- Maintain grounded prompts, refusal behavior, and citation validation.

## Team Member 3: Frontend and Evaluation Lead

- Own React upload panel, chat UI, settings, citations, and source cards.
- Prepare test questions and demo script.
- Evaluate answer quality, citation accuracy, and no-answer behavior.
- Support final presentation.

## Shared Workflow

- Branches: `main`, `dev`, `backend`, `rag-pipeline`, `frontend`.
- Use GitHub Issues with labels: `backend`, `frontend`, `rag-pipeline`, `evaluation`, `documentation`, `bug`, `enhancement`, `decision-needed`, `blocked`.
- Pull requests should include what changed, how it was tested, and known limitations.
