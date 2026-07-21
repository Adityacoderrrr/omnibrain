"""
Smoke tests for Day 2 scaffolding: app boots and core endpoints respond...
Run with: pytest
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_rejects_non_pdf():
    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 415


def test_query_unknown_document_returns_404():
    response = client.post(
        "/query",
        json={"document_id": "does-not-exist", "question": "What is the margin trend?"},
    )
    assert response.status_code == 404
