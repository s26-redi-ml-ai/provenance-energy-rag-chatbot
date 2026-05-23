# Demo Flow

1. Start the backend.

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

2. Start the frontend.

```bash
cd frontend
npm install (skip, if already installed)
npm run dev
```

3. Upload a technical manual.
4. Show the indexed document list and chunk count.
5. Ask: `What does fault code 07 mean and how should it be fixed?`
6. Point to inline citations and source cards.
7. Expand the evidence snippet and show filename, page, chunk ID, and relevance.
8. Ask a question that is not in the manual.
9. Show the refusal response.
10. Explain that the system is designed for trust: retrieve, answer, cite, verify, or refuse.
