# Evaluation Plan

## Test Question Types

- Direct answer in one document.
- Partial answer in one document.
- No answer in the uploaded documents.
- Multi-source answer across two manuals.
- Exact fault-code query such as `F07`, `Fault 07`, or `Error 07`.
- Troubleshooting-step query.
- Hallucination trap question about a non-existent model or code.

## Metrics

- Retrieval quality: relevant chunks appear in top 5.
- Answer accuracy: answer matches the retrieved evidence.
- Citation accuracy: every factual claim has a valid source marker.
- No-answer quality: unsupported questions trigger refusal.
- Fault-code accuracy: exact code queries retrieve the correct table or section.
- UI clarity: users can inspect source cards and snippets quickly.

## Acceptance Threshold

The project is demo-ready when it retrieves relevant evidence, produces grounded answers with citations, refuses unsupported questions, and lets a user verify the answer from source cards.
