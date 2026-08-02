"""
Smoke tests for app boots and core endpoints respond.
Run with: pytest
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_index():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    assert "/docs" in response.json()["docs_url"]


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_rejects_non_pdf():
    response = client.post(
        "/documents/upload",
        files={"file": ("notes.exe", b"hello world", "application/x-msdownload")},
    )
    assert response.status_code == 415



def test_query_unknown_document_returns_404():
    response = client.post(
        "/query",
        json={"document_id": "does-not-exist", "question": "What is the margin trend?"},
    )
    assert response.status_code == 404
