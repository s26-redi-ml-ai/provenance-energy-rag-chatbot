"""Integration-style tests for the public FastAPI endpoints."""

from io import BytesIO

import pytest


def test_energy_endpoint(client):
    """Verify the project health endpoint responds successfully."""
    response = client.get("/energy")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_txt_document_and_chat_with_citation(
    client,
    fault_manual_text,
    upload_text_document,
):
    """Verify upload, indexing, chat, and citations."""
    upload = upload_text_document("voltronic_manual.txt", fault_manual_text)
    assert upload["status"] == "indexed"
    assert upload["chunks_created"] >= 1

    documents = client.get("/documents")
    assert documents.status_code == 200
    filenames = {document["filename"] for document in documents.json()}
    assert "voltronic_manual.txt" in filenames

    chat = client.post(
        "/chat",
        json={"question": "What does fault code 07 mean?", "top_k": 5, "mode": "document"},
    )
    assert chat.status_code == 200
    answer = chat.json()
    assert answer["grounded"] is True
    assert "[Source 1]" in answer["answer"]
    assert answer["sources"][0]["filename"] == "voltronic_manual.txt"
    assert answer["sources"][0]["chunk_id"].startswith(upload["document_id"])


def test_each_client_starts_with_no_indexed_documents(client):
    """Verify the autouse fixture gives every API test a clean document registry."""
    response = client.get("/documents")
    assert response.status_code == 200
    assert response.json() == []


def test_upload_rejects_unsupported_file_type(client):
    """Verify disallowed file extensions are rejected."""
    response = client.post(
        "/documents/upload",
        files={"file": ("manual.exe", b"do not index me", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_rejects_missing_file(client):
    """Verify upload validation rejects requests without the required file field."""
    response = client.post("/documents/upload")
    assert response.status_code == 422


def test_upload_rejects_empty_document(client):
    """Verify empty uploads fail with a useful error."""
    response = client.post(
        "/documents/upload",
        files={"file": ("empty.txt", b"   ", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."


def test_upload_handles_corrupted_pdf(client):
    """Verify corrupted PDF uploads fail safely."""
    response = client.post(
        "/documents/upload",
        files={"file": ("broken.pdf", BytesIO(b"%PDF-1.4 broken"), "application/pdf")},
    )
    assert response.status_code == 400


def test_upload_rejects_oversized_file(client):
    """Verify files above the configured size limit are rejected with 413."""
    twenty_six_mb_data = b"X" * (26 * 1024 * 1024)

    response = client.post(
        "/documents/upload",
        files={"file": ("oversized_solar_manual.pdf", twenty_six_mb_data, "application/pdf")},
    )

    assert response.status_code == 413
    assert "larger than" in response.json()["detail"]


def test_chat_refuses_when_no_documents_are_indexed(client):
    """Verify document mode refuses without evidence."""
    response = client.post(
        "/chat",
        json={"question": "What is the Wi-Fi password?", "mode": "document"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["grounded"] is False
    assert "could not find enough information" in payload["answer"].lower()
    assert payload["sources"] == []


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"question": "", "mode": "document"},
        {"question": "What does F07 mean?", "mode": "unsupported"},
        {"question": "What does F07 mean?", "top_k": 0, "mode": "document"},
        {"question": "What does F07 mean?", "top_k": 51, "mode": "document"},
    ],
)
def test_chat_rejects_missing_or_invalid_input(client, payload):
    """Verify chat request validation rejects missing fields and invalid values."""
    response = client.post("/chat", json=payload)
    assert response.status_code == 422


def test_general_mode_is_disabled_by_default(client):
    """Verify general mode stays disabled by default."""
    response = client.post(
        "/chat",
        json={"question": "Explain inverter overloads generally.", "mode": "general"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["grounded"] is False
    assert "ALLOW_GENERAL_KNOWLEDGE is false." in payload["warnings"]


def test_fault_code_lookup_returns_exact_matches(
    client,
    fault_manual_text,
    upload_text_document,
):
    """Verify exact fault-code lookup finds indexed evidence."""
    upload_text_document("fault_lookup_manual.txt", fault_manual_text)

    response = client.post("/fault-codes/lookup", json={"code": "07", "top_k": 5})
    assert response.status_code == 200

    payload = response.json()
    assert "07" in payload["normalized_terms"]
    assert payload["matches"]
    assert payload["matches"][0]["filename"] == "fault_lookup_manual.txt"
    assert "07" in payload["matches"][0]["matched_terms"]
    assert "Overload timeout" in payload["matches"][0]["full_text"]


def test_fault_code_lookup_returns_no_matches_for_absent_code(
    client,
    fault_manual_text,
    upload_text_document,
):
    """Verify absent codes return no matches even when other fault codes are indexed."""
    upload_text_document("fault_lookup_manual.txt", fault_manual_text)

    response = client.post("/fault-codes/lookup", json={"code": "999", "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["matches"] == []
    assert "No indexed chunk contained an exact matching fault-code term." in payload["warnings"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"code": "", "top_k": 5},
        {"code": "07", "top_k": 0},
        {"code": "07", "top_k": 26},
        {"code": "F" * 81, "top_k": 5},
    ],
)
def test_fault_code_lookup_rejects_missing_or_invalid_input(client, payload):
    """Verify fault-code lookup validates missing fields, length, and top_k range."""
    response = client.post("/fault-codes/lookup", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "suspicious_input",
    [
        "@#$!%^&*()_+{}[]|\\:;\"'<>,.?/~`",
        "' OR '1'='1 --",
        "<script>alert('hacked')</script>",
    ],
)
def test_fault_code_lookup_handles_suspicious_input_without_matches(client, suspicious_input):
    """Verify suspicious but valid-length lookup text does not crash or invent matches."""
    response = client.post("/fault-codes/lookup", json={"code": suspicious_input, "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    assert payload["matches"] == []
