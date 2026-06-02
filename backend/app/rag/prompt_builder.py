from app.models.schemas import AnswerMode
from app.rag.types import RetrievedChunk

SYSTEM_PROMPT = (
    "You are a grounded technical-support RAG assistant for solar energy systems and inverters. "
    "Answer the user's question using ONLY the provided text blocks in the retrieved context. "
    "Every factual claim must be followed by its exact citation label in square brackets. "
    "Do NOT use generic citations like '[Source 1]'. "
    "Use the literal 'Citation Label' provided in each block. "
    "Do not invent facts, fault codes, or citations not explicitly present in the context. "
    "Always advise the technician to follow manufacturer safety instructions "
    "and qualified procedures."
)


def build_grounded_prompt(question: str, retrieved: list[RetrievedChunk]) -> str:
    context = "\n\n".join(
        _format_context_block(index=index, item=item)
        for index, item in enumerate(retrieved, start=1)
    )
    return f"""{SYSTEM_PROMPT}

User question:
{question}

Retrieved context:
{context}

Answer with concise technical-support guidance.
Every factual claim must be supported by a citation."""


def build_general_prompt(question: str, mode: AnswerMode) -> str:
    return f"""General knowledge mode is enabled for mode={mode}.
Clearly state that the answer is not directly grounded in uploaded documents.
Do not invent document citations.

Question:
{question}"""


def _format_context_block(index: int, item: RetrievedChunk) -> str:
    chunk = item.chunk
    page = chunk.page if chunk.page is not None else "unknown"
    section = chunk.section or "unknown"

    tilt = getattr(item, "suggested_tilt_angle", None)
    gain = getattr(item, "estimated_irradiation_gain", None)
    confidence = getattr(item, "confidence_level", "Medium")
    citation_label = getattr(chunk, "citation_label", f"{chunk.filename}, p. {page}")

    tilt_display = f"{tilt}°" if tilt is not None else "N/A"
    gain_display = f"{gain}%" if gain is not None else "N/A"

    return (
        f"--- Retrieved Block {index} ---\n"
        f"Citation Label to Use: {citation_label}\n"
        f"Document Name: {chunk.filename}\n"
        f"Page: {page}\n"
        f"Section: {section}\n"
        f"[Solar Site Analytics]\n"
        f"- Suggested Panel Tilt Angle: {tilt_display}\n"
        f"- Estimated Solar Irradiation Gain: {gain_display}\n"
        f"- Document Confidence Level: {confidence}\n\n"
        f'Text:\n"{chunk.text}"\n'
        "----------------------------"
    )
