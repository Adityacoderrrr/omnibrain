from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ingestion.pdf_parser import parse_pdf
from app.ingestion.embedder import delete_document_vectors

client = TestClient(app)


def test_empty_pdf_validation(tmp_path):
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")

    with pytest.raises(ValueError, match="empty"):
        parse_pdf(empty_pdf)


def test_document_list_and_delete_api(tmp_path):
    pdf_content = b"%PDF-1.4 Fake test pdf content for API validation"
    
    # 1. Test Upload
    response = client.post(
        "/documents/upload",
        files={"file": ("test_manual.pdf", pdf_content, "application/pdf")}
    )
    assert response.status_code == 202
    data = response.json()
    doc_id = data["document_id"]
    assert data["filename"] == "test_manual.pdf"

    # 2. Test List Documents
    list_resp = client.get("/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json()["documents"]
    assert any(d["document_id"] == doc_id for d in docs)

    # 3. Test Delete Document
    del_resp = client.delete(f"/documents/{doc_id}")
    assert del_resp.status_code == 200
    assert "successfully deleted" in del_resp.json()["message"]

    # Verify deleted from list
    list_resp2 = client.get("/documents")
    docs2 = list_resp2.json()["documents"]
    assert not any(d["document_id"] == doc_id for d in docs2)


def test_delete_document_vectors_mock():
    with patch("app.ingestion.embedder.get_qdrant_client") as mock_get_client:
        mock_qdrant = MagicMock()
        mock_get_client.return_value = mock_qdrant
        delete_document_vectors("doc-xyz-123")
        assert mock_qdrant.delete.call_count >= 1


def test_multi_format_parsing(tmp_path):
    from app.ingestion.pdf_parser import parse_document, RegionType
    
    # 1. Text file
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("This is sample text content for RAG testing.", encoding="utf-8")
    regions = parse_document(txt_file)
    assert len(regions) == 1
    assert regions[0].region_type == RegionType.TEXT
    assert "sample text content" in regions[0].content

    # 2. Markdown file
    md_file = tmp_path / "sample.md"
    md_file.write_text("# Title\n\nMarkdown paragraph text.", encoding="utf-8")
    md_regions = parse_document(md_file)
    assert len(md_regions) == 1
    assert "Markdown paragraph text" in md_regions[0].content

