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

    TODO (Day 3): implement using a layout-aware parser (e.g. Unstructured)
    to split each page into text / table / chart regions with bounding boxes.
    """
    raise NotImplementedError("PDF parsing lands on Day 3 of Week 1.")
