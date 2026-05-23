from __future__ import annotations

import os
import re
import time
from typing import Any

import httpx
import streamlit as st

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MODES = ["document", "hybrid", "general"]

# ── PAGE CONFIGURATION ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Energy RAG Support",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── SYSTEM STYLING (RESPONSIVE EMOTION THEME ENGINE) ──────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap');

    :root {
        /* Signature Brand Accent Palette - Scaled for high contrast across themes */
        --brand:      #128A6B;
        --brand-mid:  #1D9E75;
        --brand-pale: rgba(29, 158, 117, 0.12);
        
        /* Bound Surfaces Directly to Native Streamlit Theme Framework */
        --surface-0: var(--background-color);
        --surface-1: var(--secondary-background-color);
        --surface-2: rgba(128, 128, 128, 0.08);

        /* Adaptive Borders */
        --border:     rgba(128, 128, 128, 0.14);
        --border-med: rgba(128, 128, 128, 0.28);

        /* Dynamic Typography Ink Pipelines */
        --ink-1: var(--text-color);
        --ink-2: var(--text-color);
        --ink-3: var(--text-color);

        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;

        --font: 'DM Sans', 'Segoe UI', sans-serif;
    }

    /* Target-scoped typography updates to prevent clobbering system icon font sheets */
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp label, .stApp button, .stApp input {
        font-family: var(--font);
        -webkit-font-smoothing: antialiased;
    }

    /* Global canvas layout corrections */
    .stApp {
        background: var(--surface-0);
        color: var(--ink-1);
    }

    /* Responsive Sidebar Architecture */
    [data-testid="stSidebar"] {
        background: var(--surface-1);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 2rem 1.25rem;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stTextInput label {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.4rem !important;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: var(--surface-0) !important;
        border: 1px solid var(--border-med) !important;
        border-radius: var(--radius-sm) !important;
        font-size: 0.85rem !important;
        color: var(--ink-1) !important;
    }

    [data-testid="stSidebar"] input:focus {
        border-color: var(--brand-mid) !important;
        box-shadow: 0 0 0 3px rgba(29, 158, 117, 0.18) !important;
    }

    [data-testid="stSidebar"] [data-testid="stSlider"] div[role="slider"],
    [data-testid="stSidebar"] [data-testid="stSlider"] div[data-testid="stSliderThumb"] {
        background: var(--brand) !important;
        border-color: var(--brand) !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] section {
        background: rgba(128, 128, 128, 0.04);
        border: 1.5px dashed var(--border-med);
        border-radius: var(--radius-md);
        padding: 1rem;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] section:hover {
        border-color: var(--brand-mid);
    }

    [data-testid="stSidebar"] button[kind="primary"] {
        background: var(--brand) !important;
        color: #ffffff !important; /* Keep text white for maximum action visibility contrast */
        border: none !important;
        border-radius: var(--radius-sm) !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease;
    }
    
    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background: var(--brand-mid) !important;
        box-shadow: 0 2px 8px rgba(29, 158, 117, 0.3);
    }

    .stApp > section > div > div > div {
        padding-top: 2rem;
        max-width: 1150px;
    }

    /* Enterprise Hero Banner Block */
    .hero {
        padding: 1.5rem;
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        background: var(--surface-1);
        margin-bottom: 1.75rem;
        display: flex;
        align-items: center;
        gap: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    .hero-icon {
        width: 48px;
        height: 48px;
        min-width: 48px;
        border-radius: var(--radius-md);
        background: var(--brand-pale);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
    }
    
    .hero h1 {
        margin: 0 0 0.25rem 0;
        font-size: 1.35rem;
        font-weight: 600;
        color: var(--ink-1);
    }
    
    .hero p {
        margin: 0;
        opacity: 0.75;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    /* Alpha-Channel Balanced Badge Engine */
    .tag {
        display: inline-flex;
        align-items: center;
        margin-right: 6px;
        margin-bottom: 6px;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        border: 1px solid transparent;
    }
    .tag-green   { background: rgba(29, 158, 117, 0.14); color: #2ecc71; border-color: rgba(29, 158, 117, 0.25); }
    .tag-blue    { background: rgba(52, 152, 219, 0.14); color: #3498db; border-color: rgba(52, 152, 219, 0.25); }
    .tag-amber   { background: rgba(243, 156, 18, 0.14); color: #f39c12; border-color: rgba(243, 156, 18, 0.25); }
    .tag-neutral { background: var(--surface-2); color: var(--ink-1); border-color: var(--border-med); }

    /* Custom RAG Citation & Context Structures */
    .evidence-card {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-left: 4px solid var(--brand-mid);
        border-radius: var(--radius-sm);
        padding: 0.95rem 1.15rem;
        margin: 0.75rem 0;
    }
    
    .evidence-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.4rem;
    }
    
    .evidence-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--ink-1);
    }
    
    .evidence-meta {
        font-size: 0.78rem;
        opacity: 0.65;
    }

    .doc-item {
        background: var(--surface-0);
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        padding: 0.6rem 0.85rem;
        margin-bottom: 0.5rem;
    }
    
    .doc-item strong {
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--ink-1);
    }
    
    .doc-item div {
        font-size: 0.74rem;
        opacity: 0.6;
        margin-top: 0.2rem;
    }

    .score-pill {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        background: var(--brand-pale);
        color: var(--brand-mid);
        border: 1px solid rgba(29, 158, 117, 0.2);
    }

    /* Core System Message Layout Adaptations */
    [data-testid="stChatMessage"] {
        background: var(--surface-1) !important;
        border-radius: var(--radius-md) !important;
        padding: 1.15rem 1.35rem !important;
        margin-bottom: 0.85rem !important;
        border: 1px solid var(--border) !important;
    }
    
    [data-testid="stChatMessage"] p {
        font-size: 0.94rem !important;
        line-height: 1.6 !important;
    }

    [data-testid="stMarkdownContainer"] h4 {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        opacity: 0.7;
        margin: 1.5rem 0 0.65rem !important;
    }
    
    [data-testid="stExpander"] {
        border-radius: var(--radius-sm) !important;
        box-shadow: none !important;
        border: 1px solid var(--border) !important;
        background: var(--surface-0) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── BACKEND API INTEGRATIONS ──────────────────────────────────────────────────

def api_get(path: str, backend_url: str) -> Any:
    """Wrapper for general GET operations."""
    with httpx.Client(timeout=15) as client:
        response = client.get(f"{backend_url.rstrip('/')}{path}")
        response.raise_for_status()
        return response.json()


def upload_document(file: Any, backend_url: str) -> dict[str, Any]:
    """Handles technical manual stream uploading and chunk generation parsing."""
    files = {"file": (file.name, file.getvalue(), file.type or "application/octet-stream")}
    with httpx.Client(timeout=120) as client:
        response = client.post(f"{backend_url.rstrip('/')}/documents/upload", files=files)
        response.raise_for_status()
        return response.json()


def ask_question(question: str, backend_url: str, mode: str, top_k: int) -> dict[str, Any]:
    """Queries the localized LLM system context embeddings."""
    payload = {"question": question, "mode": mode, "top_k": top_k}
    with httpx.Client(timeout=120) as client:
        response = client.post(f"{backend_url.rstrip('/')}/chat", json=payload)
        response.raise_for_status()
        return response.json()




def lookup_fault_code(code: str, backend_url: str, top_k: int) -> dict[str, Any]:
    """Runs an exact fault-code lookup without calling the LLM."""
    payload = {"code": code, "top_k": top_k}
    with httpx.Client(timeout=60) as client:
        response = client.post(f"{backend_url.rstrip('/')}/fault-codes/lookup", json=payload)
        response.raise_for_status()
        return response.json()


# ── UTILITY HELPERS ───────────────────────────────────────────────────────────

def sanitize_text(value: Any, default: str = "") -> str:
    """Removes invalid code control parameters safely for Markdown presentation."""
    if value is None:
        return default
    text = str(value)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def format_score(value: Any) -> int:
    """Normalizes matching vectors metrics."""
    try:
        return round(float(value or 0) * 100)
    except (TypeError, ValueError):
        return 0


def get_confidence_class(confidence: str) -> str:
    """Maps RAG operational assurance tags to color classes."""
    c = str(confidence).lower()
    if "high" in c:
        return "tag-green"
    if "med" in c:
        return "tag-blue"
    return "tag-amber"


# ── APP STATE INITIALIZATION ──────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "answer": (
                "Upload your field manuals or engineering specs in the left sidebar, "
                "then ask about diagnostic fault codes, troubleshooting workflows, or system procedures. "
                "I will verify and surface exact sourcing passages to back up the resolution steps."
            ),
            "grounded": False,
            "confidence": "low",
            "mode": "document",
            "sources": [],
            "warnings": [],
        }
    ]

if "document_cache" not in st.session_state:
    st.session_state.document_cache = []
if "last_fetch_time" not in st.session_state:
    st.session_state.last_fetch_time = 0.0


def fetch_and_cache_documents(backend_url: str, force_refresh: bool = False) -> list:
    """Saves remote pipeline listings to state to maintain ultra-snappy interface actions."""
    current_time = time.time()
    if force_refresh or (current_time - st.session_state.last_fetch_time > 8.0):
        try:
            st.session_state.document_cache = api_get("/documents", backend_url)
            st.session_state.last_fetch_time = current_time
        except Exception:
            if not st.session_state.document_cache:
                return []
    return st.session_state.document_cache



if "fault_lookup_result" not in st.session_state:
    st.session_state.fault_lookup_result = None
if "fault_lookup_error" not in st.session_state:
    st.session_state.fault_lookup_error = ""

# ── INTERFACE RENDERING LOGIC ──────────────────────────────────────────────────

def render_sources(sources: list[dict[str, Any]]) -> None:
    """Outputs modern structured citation cards beneath verified responses."""
    if not sources:
        return

    st.markdown("#### Evidence Sources")
    for source in sources:
        source_id = sanitize_text(source.get("source_id"), "Source")
        filename = sanitize_text(source.get("filename"), "Unknown file")
        page = sanitize_text(source.get("page"), "—")
        section = sanitize_text(source.get("section"), "—")
        chunk_id = sanitize_text(source.get("chunk_id"), "—")
        snippet = sanitize_text(source.get("text_snippet"))
        score = format_score(source.get("relevance_score"))

        st.markdown(
            f"""
            <div class="evidence-card">
                <div class="evidence-header">
                    <span class="evidence-title">{source_id} &mdash; {filename}</span>
                    <span class="score-pill">{score}% match</span>
                </div>
                <div class="evidence-meta">Page {page} &middot; Section {section} &middot; ID: {chunk_id}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        if snippet:
            st.caption("_Key Matching Snippet:_")
            st.info(snippet)
            
        with st.expander(f"View Full Content Chunk Context ({chunk_id})"):
            st.write(sanitize_text(source.get("full_text")))


def render_message(message: dict[str, Any]) -> None:
    """Handles standard dynamic chat printing protocols cleanly."""
    with st.chat_message(message["role"]):
        st.write(message.get("answer", ""))

        if message["role"] == "assistant":
            grounded_label = "Grounded" if message.get("grounded") else "Generative (Not Grounded)"
            grounded_cls = "tag-green" if message.get("grounded") else "tag-neutral"
            mode_label = message.get("mode", "document")
            conf_label = message.get("confidence", "low")
            conf_cls = get_confidence_class(conf_label)

            st.markdown(
                f"<span class='tag {grounded_cls}'>{grounded_label}</span>"
                f"<span class='tag tag-blue'>{mode_label} mode</span>"
                f"<span class='tag {conf_cls}'>{conf_label} confidence</span>",
                unsafe_allow_html=True,
            )

            for warning in message.get("warnings", []):
                st.warning(sanitize_text(warning))

            render_sources(message.get("sources", []))




def render_fault_lookup(result: dict[str, Any] | None) -> None:
    """Renders exact fault-code matches as a fast verification table."""
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


# ── SIDEBAR INTERFACE CONTROL SYSTEM ──────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:0.5rem;padding:0.25rem;">
            <div style="width:40px;height:40px;border-radius:10px;background:var(--brand-pale);
                        display:flex;align-items:center;justify-content:center;font-size:1.25rem;">⚡</div>
            <div>
                <div style="font-size:1rem;font-weight:600;color:var(--text-color);line-height:1.2;">Energy RAG Engine</div>
                <div style="font-size:0.75rem;color:var(--text-color);opacity:0.6;font-weight:400;">Enterprise Technical Support</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    backend_url = st.text_input("Backend Endpoint Target", DEFAULT_BACKEND_URL, help="Verify target microservice URL context.")
    mode = st.selectbox("LLM Context Strategy", MODES, index=0, help="Document restricts output strict to uploads. General acts as standard assistant.")
    top_k = st.slider("Max Evidence Chunk Fetches", min_value=1, max_value=12, value=5)

    st.divider()

    st.markdown("### Upload Engineering Manual")
    uploaded_file = st.file_uploader(
        "Manual file",
        type=["pdf", "docx", "txt", "md", "markdown"],
        label_visibility="collapsed",
        key="manual_file",
    )

    if uploaded_file:
        st.markdown(f"📎 <span style='font-size:0.8rem;'>Ready: <b>{uploaded_file.name}</b></span>", unsafe_allow_html=True)
        
        if st.button(
            "Parse & Index Document",
            type="primary",
            use_container_width=True,
            key="index_selected_document",
        ):
            with st.spinner("Processing embeddings..."):
                try:
                    result = upload_document(uploaded_file, backend_url)
                    st.success(f"Indexed safely! Created {result.get('chunks_created', 'N/A')} vector records.")
                    fetch_and_cache_documents(backend_url, force_refresh=True)
                except Exception as exc:
                    st.error(f"Ingestion Pipeline Failed: {exc}")

    st.divider()
    
    st.markdown("### Active Cluster Inventory")
    
    docs = fetch_and_cache_documents(backend_url)
    if not docs:
        st.caption("No manual data registers active. Initialize target server endpoint or submit a file above.")
    else:
        for doc in docs:
            st.markdown(
                f"""
                <div class='doc-item'>
                    <strong>{sanitize_text(doc.get('filename'))}</strong>
                    <div>{doc.get('chunks_created', 0)} vectors &middot; <span style="color:var(--brand-mid); font-weight:600;">{doc.get('status', 'active')}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
    if st.button("Clear Interactive Session", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()


# ── MAIN APPLICATION CONVERSATION ENGINE ──────────────────────────────────────

st.markdown(
    """
    <div class="hero">
        <div class="hero-icon">⚡</div>
        <div>
            <h1>Traceable Technical Knowledge Support</h1>
            <p>Enterprise retrieval framework optimized for critical grid architecture documentation, asset manuals, and compliance directives.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.container(border=True):
    st.markdown("### Fault-code exact lookup")
    st.caption(
        "Searches exact code variants in indexed manuals first, without spending an LLM API call."
    )
    with st.form("fault_code_lookup_form"):
        code_col, limit_col = st.columns([3, 1])
        with code_col:
            lookup_code = st.text_input(
                "Fault code",
                placeholder="Example: 07, F07, Error 07",
                key="fault_lookup_code",
            )
        with limit_col:
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
            use_container_width=True,
        )

    if submitted_lookup:
        if not lookup_code.strip():
            st.session_state.fault_lookup_result = None
            st.session_state.fault_lookup_error = "Enter a fault code first."
        else:
            with st.spinner("Searching exact fault-code matches..."):
                try:
                    st.session_state.fault_lookup_result = lookup_fault_code(
                        lookup_code,
                        backend_url,
                        int(lookup_limit),
                    )
                    st.session_state.fault_lookup_error = ""
                except Exception as exc:
                    st.session_state.fault_lookup_result = None
                    st.session_state.fault_lookup_error = str(exc)

    if st.session_state.fault_lookup_error:
        st.error(st.session_state.fault_lookup_error)
    render_fault_lookup(st.session_state.fault_lookup_result)


for message in st.session_state.messages:
    render_message(message)

question = st.chat_input("Query fault codes, schematic annotations, or validation protocols...")

if question:
    st.session_state.messages.append({"role": "user", "answer": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Traversing active nodes & vector spaces..."):
            try:
                response = ask_question(question, backend_url, mode, top_k)
            except Exception as exc:
                response = {
                    "answer": "An infrastructure communication failure occurred while executing vector generation lookup routines.",
                    "grounded": False,
                    "confidence": "error",
                    "mode": mode,
                    "sources": [],
                    "warnings": [str(exc)],
                }

        assistant_message = {"role": "assistant", **response}
        st.session_state.messages.append(assistant_message)
        render_message(assistant_message)
