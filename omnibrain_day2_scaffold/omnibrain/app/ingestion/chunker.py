"""
Semantic text chunking for narrative page regions.

Scope (Week 1, Day 3-4): take TEXT-type PageRegions from pdf_parser.py and
split them into semantically coherent chunks (not naive fixed-token windows)
ready for embedding.

Not yet implemented — scaffolding committed on Day 2.
"""

from dataclasses import dataclass


@dataclass
class TextChunk:
    chunk_id: str
    document_id: str
    page_number: int
    text: str


def chunk_text_regions(document_id: str, regions: list) -> list[TextChunk]:
    """
    TODO (Day 3-4): implement semantic chunking of narrative text regions.
    """
    raise NotImplementedError("Text chunking lands on Day 3-4 of Week 1.")
