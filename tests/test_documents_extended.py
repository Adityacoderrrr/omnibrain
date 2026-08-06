"""
Tests for extended document endpoints (collections, tagging, renaming, multi-format ingestion).
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_collections_api():
    response = client.post("/collections", json={"name": "Financial Documents 2026", "tags": ["finance", "annual"]})
    assert response.status_code == 201
    data = response.json()
    col_id = data["collection_id"]
    assert data["name"] == "Financial Documents 2026"

    # List collections
    list_res = client.get("/collections")
    assert list_res.status_code == 200
    assert len(list_res.json()["collections"]) >= 1

    # Delete collection
    del_res = client.delete(f"/collections/{col_id}")
    assert del_res.status_code == 200


def test_analytics_api():
    res = client.get("/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert "total_queries" in data
    assert "avg_latency_ms" in data
    assert "estimated_cost_usd" in data


def test_tracing_api():
    res = client.get("/tracing")
    assert res.status_code == 200
    assert "traces" in res.json()
