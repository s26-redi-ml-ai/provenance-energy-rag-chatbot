FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app
COPY frontend/pyproject.toml frontend/uv.lock* ./
RUN uv sync --no-dev
COPY frontend/app.py ./app.py
COPY frontend/.streamlit ./.streamlit
EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
