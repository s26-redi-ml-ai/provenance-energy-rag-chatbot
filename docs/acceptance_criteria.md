# Acceptance Criteria

1. A user can upload at least one technical PDF manual.
2. The backend extracts and chunks the document.
3. Chunks are embedded and stored in a persistent vector database.
4. A user can ask a question through the UI.
5. The system retrieves relevant document chunks.
6. The system generates an answer grounded in those chunks.
7. The answer includes valid citation markers.
8. The UI displays filename, page, chunk ID, relevance score, and snippet.
9. The chatbot refuses when information is not in the documents.
10. Tests can be run with `uv run pytest`.
11. The backend starts with `uv run uvicorn app.main:app --reload`.
12. The team can demonstrate a fault-code or troubleshooting question using a real or sample manual.
