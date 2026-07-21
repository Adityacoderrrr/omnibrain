"""
Tests for app/ingestion/pdf_parser.py (Day 3).
"""

from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.ingestion.pdf_parser import RegionType, parse_pdf, summarize_regions


@pytest.fixture
def blank_pdf(tmp_path: Path) -> Path:
    """A minimal 2-page PDF with no extractable text, for structural checks."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    pdf_path = tmp_path / "blank.pdf"
    with open(pdf_path, "wb") as f:
        writer.write(f)
    return pdf_path


def test_parse_pdf_raises_on_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        parse_pdf(tmp_path / "does_not_exist.pdf")


def test_parse_pdf_returns_list_for_blank_pages(blank_pdf: Path):
    regions = parse_pdf(blank_pdf)
    # Blank pages produce no text/image regions — should return an empty list, not error.
    assert isinstance(regions, list)
    assert regions == []


def test_summarize_regions_counts_by_type():
    from app.ingestion.pdf_parser import PageRegion

    regions = [
        PageRegion(page_number=1, region_type=RegionType.TEXT, content="hello"),
        PageRegion(page_number=1, region_type=RegionType.TABLE, content="1  2  3"),
        PageRegion(page_number=2, region_type=RegionType.TEXT, content="world"),
    ]
    summary = summarize_regions(regions)
    assert summary == {"text": 2, "table": 1}
