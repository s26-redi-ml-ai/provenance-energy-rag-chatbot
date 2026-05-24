from io import BytesIO


def test_energy_endpoint(client):
    response = client.get("/energy")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_txt_document_and_chat_with_citation(client):
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
    response = client.post(
        "/documents/upload",
        files={"file": ("manual.exe", b"do not index me", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_rejects_empty_document(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("empty.txt", b"   ", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."


def test_upload_handles_corrupted_pdf(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("broken.pdf", BytesIO(b"%PDF-1.4 broken"), "application/pdf")},
    )
    assert response.status_code == 400


def test_chat_refuses_when_no_documents_are_indexed(client):
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
    response = client.post(
        "/chat",
        json={"question": "Explain inverter overloads generally.", "mode": "general"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["grounded"] is False
    assert "ALLOW_GENERAL_KNOWLEDGE is false." in payload["warnings"]


def test_fault_code_lookup_returns_exact_matches(client):
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
