"""Streamlit frontend for upload, chat, citations, and fault-code lookup."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import time
from typing import Any

import httpx
import streamlit as st

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MODES = ["document", "hybrid", "general"]
CHAT_CHARACTER_LIMIT = 4000
CHAT_MINIMUM_LENGTH = 2
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

    [data-testid="stChatMessage"] [data-testid="stButton"] button {
        width: 100% !important;
        height: 30px !important;
        min-height: 30px !important;
        padding: 4px 8px !important;
        border: 1px solid rgba(128, 128, 128, 0.22) !important;
        border-radius: 7px !important;
        background: rgba(18, 138, 107, 0.10) !important;
        color: #128a6b !important;
        box-shadow: none !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        line-height: 1 !important;
    }

    [data-testid="stChatMessage"] [data-testid="stButton"] button:hover {
        border-color: rgba(18, 138, 107, 0.34) !important;
        background: rgba(18, 138, 107, 0.15) !important;
        color: #0f6e56 !important;
    }

    [data-testid="stChatMessage"] [data-testid="stButton"] button p {
        color: inherit !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        line-height: 1 !important;
        margin: 0 !important;
    }

    .chat-input-notice {
        margin: 0.15rem 0 0.45rem;
        color: var(--danger);
        font-size: 0.76rem;
        font-weight: 700;
        line-height: 1.4;
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

    [data-testid="stChatInput"] {
        border: 1px solid var(--border-strong) !important;
        border-radius: var(--radius-md) !important;
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

    .starter-prompt-shell {
        border: 1px solid rgba(18, 138, 107, 0.18);
        border-radius: var(--radius-md);
        background:
            linear-gradient(135deg, rgba(18, 138, 107, 0.105), rgba(37, 99, 235, 0.055)),
            var(--surface-0);
        padding: 0.95rem 1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.045);
    }

    .starter-prompt-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.45rem;
    }

    .starter-prompt-kicker {
        color: var(--brand);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        margin-bottom: 0.18rem;
    }

    .starter-prompt-shell h3 {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 850;
        line-height: 1.2;
        margin: 0;
    }

    .starter-prompt-shell p {
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.5;
        margin: 0;
    }

    .starter-prompt-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        white-space: nowrap;
        border-radius: 999px;
        border: 1px solid rgba(37, 99, 235, 0.22);
        background: rgba(37, 99, 235, 0.10);
        color: var(--blue);
        font-size: 0.7rem;
        font-weight: 800;
        padding: 4px 9px;
    }

    .copy-help {
        color: var(--faint);
        font-size: 0.76rem;
        margin: -0.2rem 0 0.7rem;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
        background: #128a6b !important;
        border: 1px solid #128a6b !important;
        color: #ffffff !important;
        box-shadow: 0 8px 18px rgba(18, 138, 107, 0.18) !important;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]:hover {
        background: #0f6e56 !important;
        border-color: #0f6e56 !important;
        color: #ffffff !important;
        box-shadow: 0 10px 22px rgba(15, 110, 86, 0.22) !important;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] p {
        color: #ffffff !important;
    }

    .guide-panel {
        background: linear-gradient(135deg, rgba(18, 138, 107, 0.07), rgba(37, 99, 235, 0.035));
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: 1.05rem 1.15rem;
        margin-bottom: 1rem;
    }

    .guide-title {
        color: var(--brand-dark);
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }

    .guide-subtitle {
        color: var(--muted);
        font-size: 0.86rem;
        line-height: 1.45;
        margin-bottom: 0.85rem;
    }

    .guide-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.85rem;
    }

    .guide-step {
        display: grid;
        grid-template-columns: 34px minmax(0, 1fr);
        gap: 0.65rem;
        min-width: 0;
    }

    .guide-number {
        width: 34px;
        height: 34px;
        border-radius: 999px;
        background: var(--brand-soft);
        color: var(--brand);
        border: 1px solid rgba(18, 138, 107, 0.24);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        line-height: 1;
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
    }

    .guide-step strong {
        display: block;
        font-size: 0.88rem;
        line-height: 1.25;
        margin-bottom: 0.22rem;
    }

    .guide-step span {
        color: var(--muted);
        display: block;
        font-size: 0.8rem;
        line-height: 1.45;
    }

    .message-timestamp {
        color: var(--faint);
        font-size: 0.74rem;
        line-height: 1.3;
        padding-top: 0.45rem;
        text-align: right;
        white-space: nowrap;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        min-width: 0;
        overflow-wrap: anywhere;
    }

    [data-testid="stChatMessage"] button {
        min-width: 112px;
        white-space: nowrap;
    }

    @media (max-width: 980px) {
        .guide-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 640px) {
        .guide-grid {
            grid-template-columns: 1fr;
        }

        .message-timestamp {
            text-align: left;
            white-space: normal;
        }
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
    st.session_state.setdefault("chat_textarea", "")
    st.session_state.setdefault("chat_input_notice", "")


def fetch_and_cache_documents(backend_url: str, force_refresh: bool = False) -> list:
    """Cache indexed-document listings briefly to avoid unnecessary API calls."""
    current_time = time.time()
    if force_refresh or (current_time - st.session_state.last_fetch_time > 8.0):
        try:
            st.session_state.document_cache = api_get("/documents", backend_url)
            st.session_state.last_fetch_time = current_time
        except Exception:
            if not st.session_state.document_cache:
                return []
    return st.session_state.document_cache


def render_metric_cards(documents: list[dict[str, Any]], mode: str, backend_online: bool) -> None:
    """Render quick dashboard cards for demo readability."""
    document_count, chunk_count = summarize_documents(documents)
    backend_label = "Online" if backend_online else "Offline"
    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card"><strong>{document_count}</strong><span>indexed manuals</span></div>
            <div class="metric-card"><strong>{chunk_count}</strong><span>searchable chunks</span></div>
            <div class="metric-card"><strong>{backend_label}</strong><span>{mode} mode active</span></div>
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
                <div class="evidence-card">
                    <div class="evidence-header">
                        <span class="evidence-title">{source_id}: {filename}</span>
                        <span class="score-pill">{score}% match</span>
                    </div>
                    <div class="evidence-meta">Page {page} | Section {section} | Chunk {chunk_id}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if snippet:
                st.caption("Supporting snippet")
                st.info(snippet)

            with st.expander(f"Full evidence chunk ({chunk_id})", expanded=False):
                st.write(sanitize_text(source.get("full_text")))


def render_copy_answer_button(answer: str, key_seed: str) -> None:
    """Render a compact clipboard button for assistant answers."""
    if not answer:
        return

    button_id = f"copy-answer-{key_seed}"
    escaped_id = html.escape(button_id, quote=True)
    answer_json = json.dumps(answer)
    st.iframe(
        f"""
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: transparent;
            }}
        </style>
        <button id="{escaped_id}" type="button"
            style="
                width:100%;
                height:30px;
                min-height:30px;
                box-sizing:border-box;
                display:inline-flex;
                align-items:center;
                justify-content:center;
                border:1px solid rgba(128,128,128,0.22);
                border-radius:7px;
                background:rgba(18,138,107,0.10);
                color:#128a6b;
                cursor:pointer;
                font-family:DM Sans, Segoe UI, sans-serif;
                font-size:11px;
                font-weight:700;
                line-height:1;
                padding:4px 8px;
            ">
            Copy Answer
        </button>
        <script>
        const button = document.getElementById("{escaped_id}");
        button.addEventListener("click", async () => {{
            try {{
                await navigator.clipboard.writeText({answer_json});
                button.textContent = "Copied";
                setTimeout(() => button.textContent = "Copy Answer", 1400);
            }} catch (error) {{
                button.textContent = "Failed";
                setTimeout(() => button.textContent = "Copy Answer", 1400);
            }}
        }});
        </script>
        """,
        height=32,
    )


def render_message(message: dict[str, Any], index: int) -> None:
    """Render one chat message plus trust labels, copy action, and citations.

    Args:
        message: message dict from session_state
        index: position of the message in the conversation list
    """
    role = sanitize_text(message.get("role"), "assistant")
    timestamp = sanitize_text(message.get("timestamp"), time.strftime("%Y-%m-%d %H:%M"))
    with st.chat_message(role):
        answer = sanitize_text(message.get("answer", ""))

        st.markdown(
            f"<span class='chat-role-marker chat-role-{role}'></span>",
            unsafe_allow_html=True,
        )
        st.markdown(answer)

        # Action buttons and timestamp
        is_response = bool(message.get("copyable", False))
        key_seed = f"{index}-{hashlib.sha1(answer.encode('utf-8')).hexdigest()[:10]}"
        if is_response:
            copy_col, insert_col, time_col = st.columns([0.22, 0.22, 0.56])
            with copy_col:
                render_copy_answer_button(answer, key_seed)
            if insert_col.button("Insert Reply", key=f"quote-{key_seed}", width="stretch"):
                # Write directly into the chat textarea widget state so it appears immediately.
                st.session_state["chat_textarea"] = f"> {answer}\n\n"
            time_col.markdown(
                f"<div class='message-timestamp'>{timestamp}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='message-timestamp'>{timestamp}</div>",
                unsafe_allow_html=True,
            )

        # Metadata, warnings, and sources for assistant messages
        if role == "assistant":
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

    st.dataframe(rows, width="stretch", hide_index=True)

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


def queue_starter_question(question: str) -> None:
    """Store a starter question so the normal chat pipeline can process it."""
    st.session_state.pending_question = question


def submit_chat_question() -> None:
    """Queue the typed chat question and clear the input after a valid send."""
    question = sanitize_text(st.session_state.get("chat_textarea", "")).strip()
    if not question:
        st.session_state.chat_input_notice = "Type a question before sending."
        return
    if len(question) < CHAT_MINIMUM_LENGTH:
        st.session_state.chat_input_notice = "Use at least 2 characters before sending."
        return
    if len(question) > CHAT_CHARACTER_LIMIT:
        st.session_state.chat_input_notice = (
            f"Keep the question within {CHAT_CHARACTER_LIMIT:,} characters."
        )
        return
    st.session_state.chat_input_notice = ""
    st.session_state.pending_question = question
    st.session_state.chat_textarea = ""


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

    if st.button("Clear chat session", width="stretch"):
        st.session_state.messages = []
        st.session_state.fault_lookup_result = None
        st.session_state.fault_lookup_error = ""
        st.session_state.pending_question = None
        st.rerun()

question_to_process = st.session_state.pending_question
st.session_state.pending_question = None

# Top Getting Started banner (moved from the right column)
st.markdown(
    """
    <div class="guide-panel">
        <div class="guide-title">Getting Started</div>
        <div class="guide-subtitle">Quick steps to upload, index, and query your manuals. You can insert a reply as a follow-up question.</div>
        <div class="guide-grid">
            <div class="guide-step">
                <div class="guide-number">1</div>
                <div><strong>Upload</strong><span>Add manuals from the sidebar.</span></div>
            </div>
            <div class="guide-step">
                <div class="guide-number">2</div>
                <div><strong>Index</strong><span>Click <em>Index document</em> and wait for success.</span></div>
            </div>
            <div class="guide-step">
                <div class="guide-number">3</div>
                <div><strong>Ask</strong><span>Enter a question and review grounded answers.</span></div>
            </div>
            <div class="guide-step">
                <div class="guide-number">4</div>
                <div><strong>Follow up</strong><span>Use <em>Insert reply</em> to quote an answer.</span></div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.markdown(
        """
        <div class="conversation-header">
            <strong>Query and response</strong>
            <span>Ask a grounded question below. Upload manuals from the left sidebar or use starter prompts below.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for i, message in enumerate(st.session_state.messages):
        render_message(message, i)

    # The textarea stays outside a form so the character counter can update while typing.
    st.text_area(
        "Question",
        placeholder="Ask about fault codes, maintenance, troubleshooting, or source pages...",
        height=120,
        label_visibility="collapsed",
        key="chat_textarea",
        max_chars=CHAT_CHARACTER_LIMIT,
    )
    if st.session_state.chat_input_notice:
        st.markdown(
            f"<div class='chat-input-notice'>{st.session_state.chat_input_notice}</div>",
            unsafe_allow_html=True,
        )

    st.button(
        "Ask question",
        type="primary",
        width="stretch",
        on_click=submit_chat_question,
    )


with st.container(border=True):
    st.markdown("### Support tools")
    st.caption("Use starter prompts or exact fault-code lookup to explore indexed evidence.")

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
        st.markdown(
            """
            <div class="starter-prompt-shell">
                <div class="starter-prompt-header">
                    <div>
                        <div class="starter-prompt-kicker">Prompt library</div>
                        <h3>Starter prompts</h3>
                    </div>
                    <span class="starter-prompt-badge">Demo ready</span>
                </div>
                <p>Click a focused technical question to test retrieval, citations, and refusal behavior.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for row_start in range(0, len(STARTER_QUESTIONS), 2):
            starter_cols = st.columns(2)
            for offset, starter_col in enumerate(starter_cols):
                index = row_start + offset
                if index >= len(STARTER_QUESTIONS):
                    continue
                starter = STARTER_QUESTIONS[index]
                with starter_col:
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
    timestamp = time.strftime("%Y-%m-%d %H:%M")
    st.session_state.messages.append(
        {"role": "user", "answer": question_to_process, "timestamp": timestamp}
    )
    with st.spinner("Retrieving evidence, checking source strength, and drafting a grounded answer..."):
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
        {
            "role": "assistant",
            "copyable": True,
            "show_metadata": True,
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            **response,
        }
    )
    st.rerun()
