"""Integration-style tests for the public FastAPI endpoints."""

from io import BytesIO

import pytest


def test_energy_endpoint(client):
    """Verify the project health endpoint responds successfully."""
    response = client.get("/energy")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_txt_document_and_chat_with_citation(client):
    """Verify upload, indexing, chat, and citations."""
    manual = (
        "Fault Codes\n\n"
        "Fault code 07: Overload timeout. Recommended action: reduce the connected load, "
        "restart the inverter, and check whether the fault clears.\n\n"
        "Maintenance: inspect terminals only after isolating the system."
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("voltronic_manual.txt", manual.encode("utf-8"), "text/plain")},
    )
    assert upload.status_code == 201
    payload = upload.json()
    assert payload["status"] == "indexed"
    assert payload["chunks_created"] >= 1

    documents = client.get("/documents")
    assert documents.status_code == 200
    assert documents.json()[0]["filename"] == "voltronic_manual.txt"

    chat = client.post(
        "/chat",
        json={"question": "What does fault code 07 mean?", "top_k": 5, "mode": "document"},
    )
    assert chat.status_code == 200
    answer = chat.json()
    assert answer["grounded"] is True
    assert "[Source 1]" in answer["answer"]
    assert answer["sources"][0]["filename"] == "voltronic_manual.txt"
    assert answer["sources"][0]["chunk_id"].startswith(payload["document_id"])


def test_upload_rejects_unsupported_file_type(client):
    """Verify disallowed file extensions are rejected."""
    response = client.post(
        "/documents/upload",
        files={"file": ("manual.exe", b"do not index me", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


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


def test_fault_code_lookup_returns_exact_matches(client):
    """Verify exact fault-code lookup finds indexed evidence."""
    manual = (
        "Fault Codes\n\n"
        "Fault code 07: Overload timeout. Recommended action: reduce the connected load, "
        "restart the inverter, and check whether the fault clears.\n\n"
        "Fault code F12: DC bus over-voltage. Stop operation and inspect the PV input."
    )
    upload = client.post(
        "/documents/upload",
        files={"file": ("fault_lookup_manual.txt", manual.encode("utf-8"), "text/plain")},
    )
    assert upload.status_code == 201

    response = client.post("/fault-codes/lookup", json={"code": "07", "top_k": 5})
    assert response.status_code == 200

    payload = response.json()
    assert "07" in payload["normalized_terms"]
    assert payload["matches"]
    assert payload["matches"][0]["filename"] == "fault_lookup_manual.txt"
    assert "07" in payload["matches"][0]["matched_terms"]
    assert "Overload timeout" in payload["matches"][0]["full_text"]


# New Test 1: TM-1 - Uploading an Oversized File (a file larger than 25MB is rejected)
def test_upload_rejects_oversized_file(client):
    twenty_six_mb_data = b"X" * (26 * 1024 * 1024)

    response = client.post(
        "/documents/upload",
        files={"file": ("oversized_solar_manual.pdf", twenty_six_mb_data, "application/pdf")},
    )

    # 413 (Payload Too Large)
    # 400 (Bad Request)
    assert response.status_code in [413, 400]


# New Test 2: TM-1 - Fault code lookup for a non-existent code (returns empty matches)
def test_fault_code_lookup_no_matches(client):
    response = client.post("/fault-codes/lookup", json={"code": "999", "top_k": 5})

    assert response.status_code == 200
    payload = response.json()
    assert "matches" in payload
    assert payload["matches"] == []


# New Test 3: TM-1 - Security & Robustness test.
@pytest.mark.parametrize(
    "malicious_input",
    [
        "@#$!%^&*()_+{}[]|\\:;\"'<>,.?/~`",  # 1. Special characters
        "' OR '1'='1 --",  # 2. SQL Injection
        "<script>alert('hacked')</script>",  # 3. XSS Payload
        "F" * 1000,  # 4. Long string (Buffer overflow check)
    ],
)
def test_fault_code_lookup_security_sanitization(client, malicious_input):

    response = client.post("/fault-codes/lookup", json={"code": malicious_input, "top_k": 5})

    assert response.status_code in [200, 422]

    if response.status_code == 200:
        payload = response.json()
        assert "matches" in payload
        assert isinstance(payload["matches"], list)
        assert len(payload["matches"]) == 0
