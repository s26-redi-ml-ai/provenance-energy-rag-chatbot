# Contributing Guide

Thank you for contributing to the Trustworthy Domain-Specific RAG Chatbot With Provenance.

This project is a student-friendly but professionally structured RAG system for technical-support use cases. The main goal is to build a reliable assistant that answers from uploaded documents, shows provenance, and refuses unsupported answers.

## Project Values

When contributing, prioritize:

- Correctness over flashy features.
- Document-grounded answers over confident guesses.
- Clear provenance for every factual answer.
- Safe handling of technical troubleshooting information.
- Maintainable code that teammates can understand.
- uv-based Python workflows.
- Small, reviewable pull requests.

## Before You Start

Make sure you have:

- Python 3.11 or newer
- uv installed
- Git installed
- The project cloned locally
- A working backend and frontend setup

Install backend dependencies:

```bash
cd backend
uv sync
```

Install frontend dependencies:

```bash
cd frontend
uv sync
```

Do not use `python -m venv`, `pip install`, or plain `python app.py` as the main workflow for this project.

## Running The Project Locally

Start the backend:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```bash
cd frontend
uv run streamlit run app.py
```

Backend:

```text
http://localhost:8000
```

Frontend:

```text
http://localhost:8501
```

## Environment Files And Secrets

Use `.env.example` as a template:

```bash
cp .env.example .env
cp .env.example backend/.env
```

Never commit:

- Real API keys
- `.env` files
- Private manuals
- Uploaded documents
- Vector database files
- SQLite cache files
- Backend runtime data

The `.gitignore` file is configured to help prevent accidental commits, but each contributor is still responsible for checking their staged files.

Before committing, run:

```bash
git status
```

## Recommended Git Workflow

Use branches to keep work organized.

Recommended long-lived branches:

- `main`: stable demo-ready code
- `dev`: integration branch for active work

Recommended feature branches:

- `backend/<short-task-name>`
- `rag/<short-task-name>`
- `frontend/<short-task-name>`
- `docs/<short-task-name>`
- `fix/<short-task-name>`

Example:

```bash
git checkout dev
git pull
git checkout -b rag/improve-fault-code-lookup
```

After making changes:

```bash
git status
git add <files>
git commit -m "Improve fault-code exact lookup"
git push origin rag/improve-fault-code-lookup
```

Then open a pull request into `dev`.

## Pull Request Checklist

Every pull request should explain:

- What changed
- Why it changed
- How it was tested
- Any known limitations
- Screenshots if the UI changed

Before requesting review, run:

```bash
cd backend
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

For frontend changes, also run:

```bash
cd frontend
uv run python -m py_compile app.py
```

If formatting fails, run:

```bash
cd backend
uv run ruff format .
```

## Coding Standards

### Python

- Use type hints for new functions where practical.
- Keep modules focused and readable.
- Prefer small helper functions over large blocks of logic.
- Use Pydantic models for API inputs and outputs.
- Keep endpoint logic thin and put orchestration in service modules.
- Avoid hardcoded secrets, local paths, or API keys.
- Use meaningful error messages.
- Add tests for new backend behavior.

### RAG Pipeline

Changes to retrieval, chunking, embeddings, generation, or prompting must preserve the project goal: trustworthy document-grounded answers.

RAG changes should consider:

- Does this preserve filename, page, section, and chunk metadata?
- Does this improve retrieval quality?
- Does this avoid unsupported answers?
- Does this keep citation IDs valid?
- Does this work for exact technical terms like fault codes and model numbers?
- Does this reduce hallucination risk?

### Frontend

The Streamlit UI should stay:

- Clear
- Professional
- Easy for non-expert users
- Focused on document upload, chat, citations, and source verification

When adding UI features, avoid hiding provenance or making unsupported answers look authoritative.

## Trust And Safety Rules

Because this project may answer technical troubleshooting questions, contributors must follow these rules:

- Do not encourage unsafe electrical repair actions.
- Do not invent fault codes, repair steps, page numbers, document names, or citations.
- Document mode must answer only from retrieved sources.
- If evidence is weak or missing, the assistant should refuse.
- General knowledge must remain disabled by default.
- Source cards must remain visible for grounded answers.
- Keep safety warnings for high-risk electrical work.

## Adding Dependencies

Use uv.

Backend dependency:

```bash
cd backend
uv add package-name
```

Backend development dependency:

```bash
cd backend
uv add package-name --dev
```

Frontend dependency:

```bash
cd frontend
uv add package-name
```

Commit both:

- `pyproject.toml`
- `uv.lock`

Do not add a `requirements.txt` unless the team explicitly needs one for deployment compatibility.

## Testing Guidelines

Add or update tests when you change:

- API endpoints
- document loading
- chunking
- metadata preservation
- retrieval behavior
- fault-code lookup
- citation validation
- cache behavior
- refusal behavior
- environment-backed settings

Useful commands:

```bash
cd backend
uv run pytest
uv run pytest tests/test_api.py
uv run pytest tests/test_rag_units.py
```

## Documentation Guidelines

Update documentation when you change:

- setup commands
- environment variables
- endpoints
- response models
- project structure
- demo flow
- limitations
- evaluation steps

Documentation should be written for a novice teammate who is trying to run the project locally for the first time.

## Issue Labels

Suggested labels:

- `backend`
- `frontend`
- `rag-pipeline`
- `evaluation`
- `documentation`
- `bug`
- `enhancement`
- `decision-needed`
- `blocked`

## Commit Message Style

Use short, clear commit messages.

Good examples:

```text
Add fault-code lookup endpoint
Fix upload validation for empty files
Improve source card rendering
Document Docker setup
```

Avoid vague messages like:

```text
update
fix stuff
changes
final
```

## Code Review Expectations

Reviewers should check:

- Does the code solve the stated issue?
- Are tests included or updated?
- Does it preserve provenance?
- Does it avoid hallucination-prone behavior?
- Are secrets and runtime data excluded?
- Are uv workflows still documented?
- Is the UI clear and usable?

Be kind, specific, and practical in reviews.

## Resetting Local Runtime Data

To clear indexed data and start fresh:

```bash
cd backend
rm -rf data/raw data/processed data/vector_store
```

Then restart the backend and upload documents again.

Do not commit runtime data.

## Maintainer Notes

Before merging into `main`, confirm:

- Backend starts successfully.
- Frontend starts successfully.
- Tests pass.
- Lint passes.
- README and docs are current.
- No secrets or uploaded documents are staged.
- The demo flow still works.
