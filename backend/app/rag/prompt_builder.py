from app.models.schemas import AnswerMode
from app.rag.types import RetrievedChunk

SYSTEM_PROMPT = """You are a grounded technical-support RAG assistant.
Answer using only the provided context unless general knowledge mode is explicitly enabled.
If context is insufficient, say that you cannot answer from the uploaded documents.
Cite sources with the exact source IDs provided, such as [Source 1].
Do not invent facts, fault codes, troubleshooting steps, metadata, or citations.
For high-risk electrical troubleshooting, remind the user to follow manufacturer safety
instructions and qualified technician procedures."""


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
    return f"""[Source {index}]
Document: {chunk.filename}
Page: {page}
Section: {section}
Chunk ID: {chunk.chunk_id}
Relevance score: {item.relevance_score:.2f}
Text:
\"{chunk.text}\""""
