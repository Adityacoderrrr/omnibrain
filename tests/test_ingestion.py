from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from qdrant_client import QdrantClient

from app.ingestion.pdf_parser import parse_pdf, RegionType
from app.ingestion.chunker import chunk_text_regions, TextChunk
from app.ingestion.embedder import (
    ensure_collections,
    embed_and_upsert_text_chunks,
    embed_and_upsert_image_regions,
)


@pytest.fixture
def mock_pdf_reader():
    with patch("pypdf.PdfReader") as mock_reader_cls:
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Hello Paragraph 1.\n\nHello Paragraph 2. It is a long description."
        mock_page.images = []
        mock_reader.pages = [mock_page]
        mock_reader_cls.return_value = mock_reader
        yield mock_reader


def test_pdf_parsing(mock_pdf_reader):
    pdf_path = Path("fake_document.pdf")
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True
        regions = parse_pdf(pdf_path)

    assert len(regions) == 1
    assert regions[0].region_type == RegionType.TEXT
    assert "Hello Paragraph 1" in regions[0].content


def test_chunk_text_regions():
    regions = [
        MagicMock(
            region_type="text",
            page_number=1,
            content="Para 1 content.\n\nPara 2 content.",
        )
    ]
    chunks = chunk_text_regions("doc-123", regions, max_chunk_char_length=20)
    assert len(chunks) == 2
    assert chunks[0].document_id == "doc-123"
    assert chunks[0].page_number == 1
    assert chunks[0].text == "Para 1 content."
    assert chunks[1].text == "Para 2 content."



def test_indexing_pipeline():
    # Test text indexing in-memory
    client = QdrantClient(location=":memory:")
    
    # We patch get_qdrant_client to return our in-memory client
    with patch("app.ingestion.embedder.get_qdrant_client", return_value=client):
        ensure_collections(vector_size_text=1536, vector_size_image=512)
        
        chunks = [
            TextChunk(
                chunk_id="doc-123_ch_0",
                document_id="doc-123",
                page_number=1,
                text="Some test content to index.",
            )
        ]
        
        embed_and_upsert_text_chunks(chunks)
        
        res = client.scroll(collection_name="omnibrain_text")
        points = res[0]
        assert len(points) == 1
        assert points[0].payload["text"] == "Some test content to index."
        assert points[0].payload["document_id"] == "doc-123"
