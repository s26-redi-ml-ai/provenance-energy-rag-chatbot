# Streamlit Frontend

This is the simpler Python-first UI for the RAG chatbot. It replaces React + Vite so the team can work mostly in Python.

## Run

Start the FastAPI backend first:

```bash
cd ../backend
uv sync
uv run uvicorn app.main:app --reload
```

In another terminal, start Streamlit:

```bash
cd frontend
uv sync
uv run streamlit run app.py
```

Open:

```text
http://localhost:8501
```

If the backend runs somewhere else:

```bash
BACKEND_URL=http://localhost:8000 uv run streamlit run app.py
```
