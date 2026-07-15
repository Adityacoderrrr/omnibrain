"""
PDF parsing & layout analysis.

Scope (Week 1, Day 3): split an uploaded PDF into per-page regions classified
as narrative text, table, or chart/image, so downstream chunking (chunker.py)
and embedding (embedder.py) can treat each modality correctly.

Not yet implemented — this module is scaffolding committed on Day 2 so the
ingestion package structure is in place before the parsing logic lands.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


import pypdf

class RegionType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    CHART = "chart"
    HEADER_FOOTER = "header_footer"


@dataclass
class PageRegion:
    page_number: int
    region_type: RegionType
    bounding_box: tuple[float, float, float, float] | None = None
    content: str | bytes | None = None


def parse_pdf(pdf_path: Path) -> list[PageRegion]:
    """
    Parse a PDF into classified page regions.
    Extracts text page-by-page and grabs any embedded images as CHART regions.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")

    regions: list[PageRegion] = []
    reader = pypdf.PdfReader(pdf_path)

    for idx, page in enumerate(reader.pages):
        page_number = idx + 1
        text = page.extract_text() or ""
        if text.strip():
            regions.append(
                PageRegion(
                    page_number=page_number,
                    region_type=RegionType.TEXT,
                    content=text.strip(),
                )
            )

        # Basic multi-modal support: extract images on the page
        try:
            if hasattr(page, "images") and page.images:
                for img in page.images:
                    regions.append(
                        PageRegion(
                            page_number=page_number,
                            region_type=RegionType.CHART,
                            content=img.data,
                        )
                    )
        except Exception:
            pass

    return regions

