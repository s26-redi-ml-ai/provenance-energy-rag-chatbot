"""Streamlit frontend for upload, chat, citations, and fault-code lookup."""

from __future__ import annotations

import hashlib
import html
import json
import os
import pathlib
import re
import time
from typing import Any

import httpx
import streamlit as st

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MODES = ["document", "hybrid", "general"]
STARTER_QUESTIONS = [
    "What does fault code 07 mean?",
    "Which troubleshooting steps are listed for overload?",
    "What maintenance steps are required before inspection?",
    "What information is missing from the uploaded documents?",
]

st.set_page_config(
    page_title="Energy RAG Support",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');

    :root {
        --brand: #128a6b;
        --brand-dark: #0b5f4a;
        --brand-soft: rgba(18, 138, 107, 0.13);
        --blue: #2563eb;
        --blue-soft: rgba(37, 99, 235, 0.12);
        --amber: #b7791f;
        --amber-soft: rgba(245, 158, 11, 0.16);
        --danger: #b42318;
        --danger-soft: rgba(244, 63, 94, 0.12);
        --surface-0: var(--background-color);
        --surface-1: var(--secondary-background-color);
        --surface-2: rgba(128, 128, 128, 0.07);
        --border: rgba(128, 128, 128, 0.16);
        --border-strong: rgba(128, 128, 128, 0.28);
        --ink: var(--text-color);
        --muted: color-mix(in srgb, var(--text-color) 68%, transparent);
        --faint: color-mix(in srgb, var(--text-color) 48%, transparent);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --shadow-soft: 0 10px 30px rgba(15, 23, 42, 0.06);
        --font: 'DM Sans', 'Segoe UI', sans-serif;
    }

    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp label, .stApp button, .stApp input, .stApp textarea {
        font-family: var(--font);
        -webkit-font-smoothing: antialiased;
    }

    .stApp {
        color: var(--ink);
        background:
            radial-gradient(circle at 4% 0%, rgba(18, 138, 107, 0.11), transparent 26rem),
            radial-gradient(circle at 100% 0%, rgba(37, 99, 235, 0.08), transparent 28rem),
            var(--surface-0);
    }

    .stApp > section > div > div > div {
        padding-top: 1.45rem;
        max-width: 1180px;
    }

    [data-testid="stSidebar"] {
        background: var(--surface-1);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 1.4rem 1.15rem;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stTextInput label {
        font-size: 0.74rem !important;
        font-weight: 700 !important;
        opacity: 0.76;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: var(--surface-0) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius-sm) !important;
        font-size: 0.86rem !important;
        color: var(--ink) !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] section {
        background: rgba(128, 128, 128, 0.045);
        border: 1.5px dashed var(--border-strong);
        border-radius: var(--radius-md);
        padding: 1rem;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] section:hover {
        border-color: var(--brand);
    }

    .brand-card {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0.2rem 0.1rem 0.4rem;
    }

    .brand-mark {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        background: linear-gradient(135deg, var(--brand), var(--blue));
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-weight: 800;
        letter-spacing: 0.02em;
    }

    .brand-title {
        font-size: 1rem;
        font-weight: 800;
        line-height: 1.15;
    }

    .brand-subtitle {
        color: var(--faint);
        font-size: 0.76rem;
        margin-top: 0.12rem;
    }

    .hero {
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        background: linear-gradient(135deg, rgba(18, 138, 107, 0.14), rgba(37, 99, 235, 0.09));
        padding: 1.35rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-soft);
    }

    .hero h1 {
        margin: 0 0 0.35rem 0;
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.015em;
    }

    .hero p {
        margin: 0;
        color: var(--muted);
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .flow-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.65rem;
        margin-top: 1rem;
    }

    @media (max-width: 800px) {
        .flow-grid { grid-template-columns: 1fr; }
    }

    .flow-step, .metric-card, .empty-state, .trust-strip, .lookup-card {
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        background: color-mix(in srgb, var(--surface-1) 88%, transparent);
        padding: 0.85rem 1rem;
    }

    .flow-step strong {
        display: block;
        font-size: 0.84rem;
        margin-bottom: 0.18rem;
    }

    .flow-step span, .metric-card span, .empty-state p {
        color: var(--muted);
        font-size: 0.78rem;
        line-height: 1.45;
    }

    .metric-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.65rem;
        margin-bottom: 1rem;
    }

    @media (max-width: 800px) {
        .metric-grid { grid-template-columns: 1fr; }
    }

    .metric-card strong {
        display: block;
        font-size: 1.15rem;
        line-height: 1.1;
        margin-bottom: 0.18rem;
    }

    .empty-state {
        text-align: center;
        padding: 1.25rem;
        margin: 0.75rem 0;
    }

    .empty-state h3 {
        margin: 0 0 0.35rem 0;
        font-size: 1rem;
    }

    .conversation-header {
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        background: linear-gradient(135deg, rgba(18, 138, 107, 0.10), rgba(37, 99, 235, 0.07));
        padding: 1.05rem 1.15rem;
        margin-bottom: 0.9rem;
    }

    .conversation-header strong {
        display: block;
        color: var(--ink);
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.015em;
        line-height: 1.18;
        margin-bottom: 0.32rem;
    }

    .conversation-header span {
        color: var(--muted);
        display: block;
        font-size: 0.92rem;
        line-height: 1.52;
    }

    .tag {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        margin-right: 6px;
        margin-bottom: 6px;
        padding: 4px 11px;
        border-radius: 999px;
        font-size: 0.74rem;
        font-weight: 700;
        border: 1px solid transparent;
        max-width: 100%;
        white-space: normal;
        overflow-wrap: anywhere;
    }

    .tag-green { background: var(--brand-soft); color: var(--brand); border-color: rgba(18, 138, 107, 0.28); }
    .tag-blue { background: var(--blue-soft); color: var(--blue); border-color: rgba(37, 99, 235, 0.24); }
    .tag-amber { background: var(--amber-soft); color: var(--amber); border-color: rgba(245, 158, 11, 0.28); }
    .tag-red { background: var(--danger-soft); color: var(--danger); border-color: rgba(244, 63, 94, 0.22); }
    .tag-neutral { background: var(--surface-2); color: var(--ink); border-color: var(--border-strong); }

    .doc-item {
        background: var(--surface-0);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 0.65rem 0.78rem;
        margin-bottom: 0.55rem;
    }

    .doc-item strong {
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--ink);
        overflow-wrap: anywhere;
    }

    .doc-item div {
        color: var(--faint);
        font-size: 0.73rem;
        margin-top: 0.22rem;
    }

    .evidence-card {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-left: 4px solid var(--brand);
        border-radius: var(--radius-md);
        padding: 0.9rem 1rem;
        margin: 0.75rem 0 0.45rem;
    }

    .evidence-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.35rem;
    }

    .evidence-title {
        color: var(--ink);
        font-size: 0.88rem;
        font-weight: 800;
        overflow-wrap: anywhere;
    }

    .evidence-meta {
        color: var(--faint);
        font-size: 0.75rem;
        line-height: 1.45;
    }

    .score-pill {
        display: inline-flex;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 800;
        background: var(--brand-soft);
        color: var(--brand);
        border: 1px solid rgba(18, 138, 107, 0.24);
    }

    .starter-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.55rem;
        margin: 0.85rem 0 1rem;
    }

    @media (max-width: 800px) {
        .starter-grid { grid-template-columns: 1fr; }
    }

    .trust-strip {
        margin: 0.7rem 0;
    }

    [data-testid="stChatMessage"] {
        background: var(--surface-1) !important;
        border-radius: var(--radius-md) !important;
        padding: 1.08rem 1.25rem !important;
        margin-bottom: 0.85rem !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.035);
    }

    [data-testid="stChatMessage"]:has(.chat-role-user) {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.13), rgba(37, 99, 235, 0.045)) !important;
        border-color: rgba(37, 99, 235, 0.24) !important;
    }

    [data-testid="stChatMessage"]:has(.chat-role-assistant) {
        background: linear-gradient(135deg, rgba(18, 138, 107, 0.13), rgba(18, 138, 107, 0.045)) !important;
        border-color: rgba(18, 138, 107, 0.24) !important;
    }

    .chat-role-marker {
        display: none;
    }

    [data-testid="stChatMessage"] p {
        font-size: 0.94rem !important;
        line-height: 1.62 !important;
    }

    [data-testid="stMarkdownContainer"] h4 {
        font-size: 0.78rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        opacity: 0.72;
        margin: 1.2rem 0 0.55rem !important;
    }

    [data-testid="stExpander"] {
        border-radius: var(--radius-sm) !important;
        box-shadow: none !important;
        border: 1px solid var(--border) !important;
        background: var(--surface-0) !important;
    }


    .mode-note {
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        background: var(--surface-0);
        color: var(--muted);
        font-size: 0.8rem;
        line-height: 1.45;
        padding: 0.62rem 0.72rem;
        margin: 0.45rem 0 0.7rem;
        overflow-wrap: anywhere;
        white-space: normal;
    }

    .mode-warning {
        border-left: 4px solid var(--amber);
        border-radius: var(--radius-sm);
        background: var(--amber-soft);
        color: var(--amber);
        font-size: 0.78rem;
        font-weight: 700;
        line-height: 1.45;
        padding: 0.58rem 0.72rem;
        margin-bottom: 0.75rem;
        overflow-wrap: anywhere;
    }

    .panel-note {
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        background: color-mix(in srgb, var(--surface-1) 82%, transparent);
        color: var(--muted);
        font-size: 0.8rem;
        line-height: 1.55;
        padding: 0.75rem 0.85rem;
        margin: 0.65rem 0 1rem;
    }

    .copy-help {
        color: var(--faint);
        font-size: 0.76rem;
        margin: -0.2rem 0 0.7rem;
    }

    button[kind="primary"] {
        background: var(--brand) !important;
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-weight: 800 !important;
    }

    /* 1. Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 0.6rem 0;
    }
    .typing-indicator span {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--brand);
        animation: bounce 1.2s infinite ease-in-out;
    }
    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }

    /* 2. Empty chat state */
    .chat-empty-state {
        text-align: center;
        padding: 2.5rem 1rem;
        color: var(--faint);
    }
    .chat-empty-state .empty-icon {
        font-size: 2.4rem;
        margin-bottom: 0.65rem;
    }
    .chat-empty-state h3 {
        font-size: 1rem;
        font-weight: 700;
        color: var(--muted);
        margin: 0 0 0.3rem;
    }
    .chat-empty-state p {
        font-size: 0.84rem;
        color: var(--faint);
        margin: 0;
    }

    /* 3. Confidence border on chat bubbles */
    [data-testid="stChatMessage"]:has(.confidence-high) {
        border-left: 4px solid var(--brand) !important;
    }
    [data-testid="stChatMessage"]:has(.confidence-medium) {
        border-left: 4px solid var(--blue) !important;
    }
    [data-testid="stChatMessage"]:has(.confidence-low) {
        border-left: 4px solid var(--amber) !important;
    }
    [data-testid="stChatMessage"]:has(.confidence-error) {
        border-left: 4px solid var(--danger) !important;
    }
    .confidence-marker { display: none; }

    /* 4. Fade-in animation on new messages */
    [data-testid="stChatMessage"] {
        animation: fadeSlideIn 0.25s ease-out;
    }
    @keyframes fadeSlideIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* 5. Character count hint */
    .char-count {
        font-size: 0.74rem;
        color: var(--faint);
        text-align: right;
        margin-top: -0.3rem;
        margin-bottom: 0.4rem;
    }
    .char-count.near-limit { color: var(--amber); }

    /* 6. Collapsible hero toggle */
    .hero-toggle {
        font-size: 0.76rem;
        color: var(--brand);
        cursor: pointer;
        font-weight: 700;
        text-align: right;
        display: block;
        margin-top: 0.5rem;
    }

    /* 7. Source cards styling */
    .source-card {
        background: var(--surface-0);
        border: 1px solid var(--border);
        border-left: 4px solid var(--brand);
        border-radius: var(--radius-md);
        padding: 0.85rem 1rem;
        margin: 0.5rem 0;
    }
    .source-card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.5rem;
        margin-bottom: 0.3rem;
    }
    .source-card-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: var(--ink);
        overflow-wrap: anywhere;
    }
    .source-card-meta {
        font-size: 0.74rem;
        color: var(--faint);
        margin-bottom: 0.4rem;
    }
    .source-card-snippet {
        font-size: 0.8rem;
        color: var(--muted);
        line-height: 1.5;
        border-top: 1px solid var(--border);
        padding-top: 0.4rem;
        margin-top: 0.4rem;
    }

    /* 8. Sticky chat input */
    .sticky-input-wrapper {
        position: sticky;
        bottom: 0;
        background: var(--surface-0);
        padding: 0.75rem 0 0.25rem;
        border-top: 1px solid var(--border);
        margin-top: 0.5rem;
        z-index: 10;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_get(path: str, backend_url: str) -> Any:
    """Call a backend GET endpoint and return JSON."""
    with httpx.Client(timeout=15) as client:
        response = client.get(f"{backend_url.rstrip('/')}{path}")
        response.raise_for_status()
        return response.json()


def upload_document(file: Any, backend_url: str) -> dict[str, Any]:
    """Upload a technical document to the backend ingestion endpoint."""
    files = {"file": (file.name, file.getvalue(), file.type or "application/octet-stream")}
    with httpx.Client(timeout=120) as client:
        response = client.post(f"{backend_url.rstrip('/')}/documents/upload", files=files)
        response.raise_for_status()
        return response.json()


def ask_question(question: str, backend_url: str, mode: str, top_k: int) -> dict[str, Any]:
    """Ask the backend chat endpoint for a RAG answer."""
    payload = {"question": question, "mode": mode, "top_k": top_k}
    with httpx.Client(timeout=120) as client:
        response = client.post(f"{backend_url.rstrip('/')}/chat", json=payload)
        response.raise_for_status()
        return response.json()


def lookup_fault_code(code: str, backend_url: str, top_k: int) -> dict[str, Any]:
    """Run an exact fault-code lookup without calling the LLM."""
    payload = {"code": code, "top_k": top_k}
    with httpx.Client(timeout=60) as client:
        response = client.post(f"{backend_url.rstrip('/')}/fault-codes/lookup", json=payload)
        response.raise_for_status()
        return response.json()


def api_error_message(exc: Exception) -> str:
    """Return backend validation details instead of a generic HTTP error."""
    if isinstance(exc, httpx.HTTPStatusError):
        response = exc.response
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        detail = payload.get("detail") if isinstance(payload, dict) else None
        if detail:
            return f"{response.status_code} {response.reason_phrase}: {detail}"
        return f"{response.status_code} {response.reason_phrase}: {response.text}"

    return str(exc)


def sanitize_text(value: Any, default: str = "") -> str:
    """Remove control characters and collapse spacing before rendering text."""
    if value is None:
        return default
    text = str(value)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def format_score(value: Any) -> int:
    """Convert a relevance score into a percentage."""
    try:
        return round(float(value or 0) * 100)
    except (TypeError, ValueError):
        return 0


def get_confidence_class(confidence: str) -> str:
    """Map RAG confidence labels to badge color classes."""
    c = str(confidence).lower()
    if "high" in c:
        return "tag-green"
    if "med" in c:
        return "tag-blue"
    if "error" in c:
        return "tag-red"
    return "tag-amber"


def check_backend_status(backend_url: str) -> tuple[bool, str]:
    """Return whether the backend health endpoint is reachable."""
    try:
        payload = api_get("/energy", backend_url)
    except Exception as exc:  # noqa: BLE001
        return False, api_error_message(exc)
    return payload.get("status") == "ok", "Backend is online."


def summarize_documents(documents: list[dict[str, Any]]) -> tuple[int, int]:
    """Return document and chunk counts for sidebar and dashboard cards."""
    chunk_count = 0
    for document in documents:
        try:
            chunk_count += int(document.get("chunks_created", 0))
        except (TypeError, ValueError):
            continue
    return len(documents), chunk_count


def mode_description(mode: str) -> str:
    """Describe the current answer mode in plain language."""
    if mode == "document":
        return "Answers only from uploaded manuals and refuses unsupported answers."
    if mode == "hybrid":
        return "Checks manuals first, then can add clearly labeled general context."
    return "General mode is enabled and may answer without document evidence."


def init_state() -> None:
    """Initialize Streamlit session state used across reruns."""
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("document_cache", [])
    st.session_state.setdefault("last_fetch_time", 0.0)
    st.session_state.setdefault("fault_lookup_result", None)
    st.session_state.setdefault("fault_lookup_error", "")
    st.session_state.setdefault("last_upload_result", None)
    st.session_state.setdefault("pending_question", None)
    st.session_state.setdefault("current_session_name", "")



CHAT_HISTORY_DIR = pathlib.Path("chat_history")
CHAT_HISTORY_DIR.mkdir(exist_ok=True)


def fetch_and_cache_documents(backend_url: str, force_refresh: bool = False) -> list:
    """Cache indexed-document listings briefly to avoid unnecessary API calls."""
    current_time = time.time()
    if force_refresh or (current_time - st.session_state.last_fetch_time > 8.0):
        try:
            st.session_state.document_cache = api_get("/documents", backend_url)
            st.session_state.last_fetch_time = current_time
        except Exception as exc:  # noqa: BLE001
            if not st.session_state.document_cache:
                st.warning(f"Could not load indexed documents: {api_error_message(exc)}")
                return []
    return st.session_state.document_cache


def list_chat_sessions() -> list[str]:
    """Return saved session names sorted by most recent."""
    files = sorted(CHAT_HISTORY_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [f.stem for f in files]


def save_chat_session(name: str, messages: list) -> None:
    """Save current messages to a JSON file."""
    if not name.strip():
        return
    safe_name = re.sub(r"[^\w\s-]", "", name.strip()).replace(" ", "_")
    path = CHAT_HISTORY_DIR / f"{safe_name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def load_chat_session(name: str) -> list:
    """Load messages from a saved session JSON file."""
    path = CHAT_HISTORY_DIR / f"{name}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def delete_chat_session(name: str) -> None:
    """Delete a saved session file."""
    path = CHAT_HISTORY_DIR / f"{name}.json"
    if path.exists():
        path.unlink()



    """Cache indexed-document listings briefly to avoid unnecessary API calls."""
    current_time = time.time()
    if force_refresh or (current_time - st.session_state.last_fetch_time > 8.0):
        try:
            st.session_state.document_cache = api_get("/documents", backend_url)
            st.session_state.last_fetch_time = current_time
        except Exception as exc:  # noqa: BLE001
            if not st.session_state.document_cache:
                st.warning(f"Could not load indexed documents: {api_error_message(exc)}")
                return []
    return st.session_state.document_cache


def render_metric_cards(documents: list[dict[str, Any]], mode: str, backend_online: bool) -> None:
    """Render quick dashboard cards for demo readability."""
    document_count, chunk_count = summarize_documents(documents)
    backend_label = "Online" if backend_online else "Offline"
    backend_color = "var(--brand)" if backend_online else "var(--danger)"
    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card"><strong>{document_count}</strong><span>indexed manuals</span></div>
            <div class="metric-card"><strong>{chunk_count}</strong><span>searchable chunks</span></div>
            <div class="metric-card"><strong style="color:{backend_color}">{backend_label}</strong><span>{mode} mode active</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_trust_summary(message: dict[str, Any]) -> None:
    """Render answer trust information above citations."""
    grounded = bool(message.get("grounded"))
    confidence = sanitize_text(message.get("confidence"), "low")
    sources = message.get("sources", [])
    mode = sanitize_text(message.get("mode"), "document")
    grounded_label = "Document-grounded" if grounded else "Not document-grounded"
    grounded_cls = "tag-green" if grounded else "tag-neutral"
    conf_cls = get_confidence_class(confidence)

    st.markdown(
        f"""
        <div class="trust-strip">
            <span class="tag {grounded_cls}">{grounded_label}</span>
            <span class="tag tag-blue">{mode} mode</span>
            <span class="tag {conf_cls}">{confidence} confidence</span>
            <span class="tag tag-neutral">{len(sources)} source(s)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sources(sources: list[dict[str, Any]]) -> None:
    """Render citation cards in a collapsed source viewer by default."""
    if not sources:
        return

    label = f"View sources ({len(sources)})"
    with st.expander(label, expanded=False):
        st.caption("Open this section to verify filename, page, chunk ID, and supporting text.")
        for source in sources:
            source_id = sanitize_text(source.get("source_id"), "Source")
            filename = sanitize_text(source.get("filename"), "Unknown file")
            page = sanitize_text(source.get("page"), "-")
            section = sanitize_text(source.get("section"), "-")
            chunk_id = sanitize_text(source.get("chunk_id"), "-")
            snippet = sanitize_text(source.get("text_snippet"))
            score = format_score(source.get("relevance_score"))

            st.markdown(
                f"""
                <div class="source-card">
                    <div class="source-card-header">
                        <span class="source-card-title">{source_id}: {filename}</span>
                        <span class="score-pill">{score}% match</span>
                    </div>
                    <div class="source-card-meta">Page {page} &nbsp;·&nbsp; Section {section} &nbsp;·&nbsp; Chunk {chunk_id}</div>
                    {f'<div class="source-card-snippet">{snippet}</div>' if snippet else ''}
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander(f"Full evidence chunk ({chunk_id})", expanded=False):
                st.write(sanitize_text(source.get("full_text")))


def render_copy_answer_button(answer: str, key_seed: str) -> None:
    '''Render a small clipboard button and insert reply button for assistant answers.'''
    if not answer:
        return

    button_id = f"copy-answer-{key_seed}"
    escaped_id = html.escape(button_id, quote=True)
    answer_json = json.dumps(answer)
    st.iframe(
        f"""
        <div style="display:flex;align-items:center;gap:8px;margin:0 0 8px 0;">
            <button id="{escaped_id}" type="button"
                style="
                    border:1px solid rgba(128,128,128,0.24);
                    border-radius:8px;
                    background:rgba(18,138,107,0.10);
                    color:#128a6b;
                    cursor:pointer;
                    font-family:DM Sans, Segoe UI, sans-serif;
                    font-size:12px;
                    font-weight:700;
                    padding:6px 10px;
                ">
                Copy answer
            </button>
            <span id="{escaped_id}-status"
                style="font-family:DM Sans, Segoe UI, sans-serif;font-size:12px;color:#128a6b;">
            </span>
        </div>
        <script>
        const button = document.getElementById("{escaped_id}");
        const status = document.getElementById("{escaped_id}-status");
        button.addEventListener("click", async () => {{
            try {{
                await navigator.clipboard.writeText({answer_json});
                status.textContent = "Copied";
                setTimeout(() => status.textContent = "", 1600);
            }} catch (error) {{
                status.textContent = "Copy failed";
            }}
        }});
        </script>
        """,
        height=42,
    )




def render_message(message: dict[str, Any], index: int = 0) -> None:
    """Render one chat message plus trust labels, copy action, and citations."""
    role = sanitize_text(message.get("role"), "assistant")
    confidence = sanitize_text(message.get("confidence"), "")
    conf_marker = ""
    if role == "assistant" and confidence:
        c = confidence.lower()
        if "high" in c:
            conf_marker = "<span class='confidence-marker confidence-high'></span>"
        elif "med" in c:
            conf_marker = "<span class='confidence-marker confidence-medium'></span>"
        elif "error" in c:
            conf_marker = "<span class='confidence-marker confidence-error'></span>"
        else:
            conf_marker = "<span class='confidence-marker confidence-low'></span>"

    with st.chat_message(role):
        answer = sanitize_text(message.get("answer", ""))
        st.markdown(
            f"<span class='chat-role-marker chat-role-{role}'></span>{conf_marker}",
            unsafe_allow_html=True,
        )
        st.write(answer)

        if ts := message.get("timestamp"):
            st.caption(ts)

        if message["role"] == "assistant":
            is_response = bool(message.get("copyable", False))
            if is_response:
                key_seed = f"{index}-{hashlib.sha1(answer.encode('utf-8')).hexdigest()[:10]}"
                render_copy_answer_button(answer, key_seed)

            if message.get("show_metadata", is_response):
                render_trust_summary(message)

                for warning in message.get("warnings", []):
                    st.warning(sanitize_text(warning))

                render_sources(message.get("sources", []))


def render_fault_lookup(result: dict[str, Any] | None) -> None:
    """Render exact fault-code matches as a fast verification table."""
    if not result:
        return

    for warning in result.get("warnings", []):
        st.warning(sanitize_text(warning))

    matches = result.get("matches", [])
    if not matches:
        st.info("No exact fault-code match was found in the indexed manuals.")
        return

    rows = []
    for match in matches:
        rows.append(
            {
                "Match": sanitize_text(match.get("source_id")),
                "File": sanitize_text(match.get("filename")),
                "Page": sanitize_text(match.get("page"), "-"),
                "Section": sanitize_text(match.get("section"), "-"),
                "Chunk": sanitize_text(match.get("chunk_id")),
                "Score": f"{format_score(match.get('relevance_score'))}%",
                "Terms": ", ".join(match.get("matched_terms", [])),
                "Snippet": sanitize_text(match.get("text_snippet")),
            }
        )

    st.dataframe(rows, use_container_width=True, hide_index=True)

    for match in matches:
        label = (
            f"{sanitize_text(match.get('source_id'))}: "
            f"{sanitize_text(match.get('filename'))} | "
            f"page {sanitize_text(match.get('page'), '-')}"
        )
        with st.expander(label):
            st.caption(
                "Chunk "
                f"{sanitize_text(match.get('chunk_id'))} | "
                f"matched: {', '.join(match.get('matched_terms', []))}"
            )
            st.write(sanitize_text(match.get("full_text")))


init_state()

with st.sidebar:
    st.markdown(
        """
        <div class="brand-card">
            <div class="brand-mark">ER</div>
            <div>
                <div class="brand-title">Energy RAG Support</div>
                <div class="brand-subtitle">Grounded manual assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    backend_url = st.text_input(
        "Backend URL",
        DEFAULT_BACKEND_URL,
        help="FastAPI service used by the Streamlit frontend.",
    )
    backend_online, backend_message = check_backend_status(backend_url)
    status_class = "tag-green" if backend_online else "tag-red"
    status_label = "Backend online" if backend_online else "Backend offline"
    st.markdown(f"<span class='tag {status_class}'>{status_label}</span>", unsafe_allow_html=True)
    if not backend_online:
        st.caption(backend_message)

    mode = st.selectbox(
        "Answer mode",
        MODES,
        index=0,
        help="Document mode is safest: it answers only from uploaded manuals.",
    )
    st.markdown(
        f"<div class='mode-note'>{mode_description(mode)}</div>",
        unsafe_allow_html=True,
    )
    if mode == "general":
        st.markdown(
            "<div class='mode-warning'>General answers are useful for quick context, "
            "but they are not document-grounded unless source cards appear.</div>",
            unsafe_allow_html=True,
        )
    top_k = st.slider(
        "Evidence chunks",
        min_value=1,
        max_value=12,
        value=5,
        help=(
            "How many relevant document chunks the backend retrieves for each question. "
            "Higher values can improve context but may make responses slower."
        ),
    )

    st.divider()

    st.markdown("### Upload manual")
    st.caption("Supports PDF, DOCX, TXT, and Markdown.")
    uploaded_file = st.file_uploader(
        "Manual file",
        type=["pdf", "docx", "txt", "md", "markdown"],
        label_visibility="collapsed",
        key="manual_file",
    )

    if uploaded_file:
        st.caption(f"Ready to index: **{uploaded_file.name}**")

        if st.button(
            "Index document",
            type="primary",
            width="stretch",
            key="index_selected_document",
        ):
            with st.spinner("Saving document, extracting text, and creating embeddings..."):
                try:
                    result = upload_document(uploaded_file, backend_url)
                    st.session_state.last_upload_result = result
                    fetch_and_cache_documents(backend_url, force_refresh=True)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Ingestion failed: {api_error_message(exc)}")

    if st.session_state.last_upload_result:
        result = st.session_state.last_upload_result
        st.success(
            f"Indexed {result.get('filename')} "
            f"with {result.get('chunks_created', 'N/A')} chunks."
        )
        st.session_state.last_upload_result = None

    st.divider()

    st.subheader(
        "Indexed documents",
        help=(
            "Manuals that have already been uploaded, extracted, chunked, embedded, "
            "and stored for retrieval."
        ),
    )
    docs = fetch_and_cache_documents(backend_url)
    document_count, chunk_count = summarize_documents(docs)
    st.markdown(
        f"<span class='tag tag-green'>{document_count} manual(s)</span>"
        f"<span class='tag tag-blue'>{chunk_count} chunk(s)</span>",
        unsafe_allow_html=True,
    )

    if not docs:
        st.caption("No manuals indexed yet. Upload a document to begin.")
    else:
        with st.expander(f"View {document_count} indexed manual(s)", expanded=False):
            for doc in docs:
                st.markdown(
                    f"""
                    <div class='doc-item'>
                        <strong>{sanitize_text(doc.get('filename'))}</strong>
                        <div>{doc.get('chunks_created', 0)} chunks | {doc.get('status', 'indexed')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.divider()
    st.markdown("### Chat history")

    session_name = st.text_input(
        "Session name",
        value=st.session_state.current_session_name,
        placeholder="e.g. Fault code review",
        key="session_name_input",
        label_visibility="collapsed",
    )

    col_save, col_new = st.columns(2)
    with col_save:
        if st.button("Save session", width="stretch", key="save_session_btn"):
            if session_name.strip():
                save_chat_session(session_name, st.session_state.messages)
                st.session_state.current_session_name = session_name.strip()
                st.success("Session saved.")
            else:
                st.warning("Enter a session name first.")

    with col_new:
        if st.button("New session", width="stretch", key="new_session_btn"):
            if st.session_state.messages and st.session_state.current_session_name:
                save_chat_session(st.session_state.current_session_name, st.session_state.messages)
            st.session_state.messages = []
            st.session_state.current_session_name = ""
            st.session_state.fault_lookup_result = None
            st.session_state.fault_lookup_error = ""
            st.session_state.pending_question = None
            st.rerun()

    saved_sessions = list_chat_sessions()
    if saved_sessions:
        selected_session = st.selectbox(
            "Load a previous session",
            options=["— select —"] + saved_sessions,
            key="load_session_select",
        )
        col_load, col_del = st.columns(2)
        with col_load:
            if st.button("Load", width="stretch", key="load_session_btn"):
                if selected_session != "— select —":
                    st.session_state.messages = load_chat_session(selected_session)
                    st.session_state.current_session_name = selected_session
                    st.session_state.fault_lookup_result = None
                    st.session_state.fault_lookup_error = ""
                    st.rerun()
        with col_del:
            if st.button("Delete", width="stretch", key="delete_session_btn"):
                if selected_session != "— select —":
                    delete_chat_session(selected_session)
                    st.success(f"Deleted '{selected_session}'.")
                    st.rerun()

    if st.button("Clear chat session", width="stretch"):
        st.session_state.messages = []
        st.session_state.fault_lookup_result = None
        st.session_state.fault_lookup_error = ""
        st.session_state.pending_question = None
        st.rerun()

question_to_process = st.session_state.pending_question
st.session_state.pending_question = None

st.session_state.setdefault("show_hero", True)

if st.session_state.show_hero:
    st.markdown(
        """
        <div class="hero">
            <strong>Getting Started</strong>
            <p>Quick steps to upload, index, and query your manuals.</p>
            <div class="flow-grid" style="grid-template-columns: repeat(4, minmax(0, 1fr));">
                <div class="flow-step"><strong>1. Upload</strong><span>Add manuals from the sidebar.</span></div>
                <div class="flow-step"><strong>2. Index</strong><span>Click <em>Index document</em> and wait for success.</span></div>
                <div class="flow-step"><strong>3. Ask</strong><span>Enter a question and review grounded answers.</span></div>
                <div class="flow-step"><strong>4. Load previous session</strong><span>Use <em>Chat history</em> in the sidebar to reload past conversations.</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Hide guide ▲", key="hide_hero"):
        st.session_state.show_hero = False
        st.rerun()
else:
    if st.button("Show guide ▼", key="show_hero_btn"):
        st.session_state.show_hero = True
        st.rerun()

chat_col, right_col = st.columns([1.55, 0.9], gap="large")

with chat_col:
    with st.container(border=True):
        st.markdown(
            """
            <div class="conversation-header">
                <strong>Query and response</strong>
                <span>Ask a grounded question below. Upload manuals from the left or use starter prompts on the right.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not st.session_state.messages:
            st.markdown(
                """
                <div class="chat-empty-state">
                    <div class="empty-icon">⚡</div>
                    <h3>No questions yet</h3>
                    <p>Ask your first question below or pick a starter prompt on the right.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for index, message in enumerate(st.session_state.messages):
                render_message(message, index)

        chat_question = st.chat_input(
            "Ask about fault codes, maintenance, troubleshooting, or source pages...",
            key="chat_input_text",
        )

        if chat_question and chat_question.strip():
            question_to_process = chat_question.strip()

with right_col:
    render_metric_cards(docs, mode, backend_online)

    if not docs:
        st.markdown(
            """
            <div class="empty-state">
                <h3>No manuals indexed</h3>
                <p>Upload a technical manual in the left sidebar before asking document-mode questions.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.markdown("### Starter prompts")
        st.caption("Send one of these into the middle query workspace.")
        for index, starter in enumerate(STARTER_QUESTIONS):
            if st.button(starter, width="stretch", key=f"starter_{index}"):
                question_to_process = starter

    with st.container(border=True):
        st.markdown("### Exact fault-code lookup")
        st.caption("Searches exact code variants in indexed manuals without spending an LLM API call.")
        with st.form("fault_code_lookup_form"):
            lookup_code = st.text_input(
                "Fault code",
                placeholder="Example: 07, F07, Error 07",
                key="fault_lookup_code",
            )
            lookup_limit = st.number_input(
                "Matches",
                min_value=1,
                max_value=25,
                value=10,
                step=1,
                key="fault_lookup_limit",
            )
            submitted_lookup = st.form_submit_button(
                "Lookup code",
                type="primary",
                width="stretch",
            )

        if submitted_lookup:
            if not lookup_code.strip():
                st.session_state.fault_lookup_result = None
                st.session_state.fault_lookup_error = "Enter a fault code first."
            else:
                with st.spinner("Searching indexed chunks for exact fault-code evidence..."):
                    try:
                        st.session_state.fault_lookup_result = lookup_fault_code(
                            lookup_code,
                            backend_url,
                            int(lookup_limit),
                        )
                        st.session_state.fault_lookup_error = ""
                    except Exception as exc:  # noqa: BLE001
                        st.session_state.fault_lookup_result = None
                        st.session_state.fault_lookup_error = api_error_message(exc)

        if st.session_state.fault_lookup_error:
            st.error(st.session_state.fault_lookup_error)
        render_fault_lookup(st.session_state.fault_lookup_result)

if question_to_process:
    message_time = time.strftime("%d.%m.%Y %H:%M")
    st.session_state.messages.append({"role": "user", "answer": question_to_process, "timestamp": message_time})

    with chat_col:
        typing_placeholder = st.empty()
        with typing_placeholder:
            with st.chat_message("assistant"):
                st.markdown(
                    """
                    <div class="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    try:
        response = ask_question(question_to_process, backend_url, mode, top_k)
    except Exception as exc:  # noqa: BLE001
        response = {
            "answer": "The backend could not process that request.",
            "grounded": False,
            "confidence": "error",
            "mode": mode,
            "sources": [],
            "warnings": [api_error_message(exc)],
        }

    st.session_state.messages.append(
        {"role": "assistant", "copyable": True, "show_metadata": True, "timestamp": message_time, **response}
    )
    if st.session_state.current_session_name:
        save_chat_session(st.session_state.current_session_name, st.session_state.messages)
    st.rerun()
