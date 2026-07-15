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


def chunk_text_regions(document_id: str, regions: list, max_chunk_char_length: int = 1000, overlap_paragraphs: int = 0) -> list[TextChunk]:
    """
    Split text regions into semantically coherent paragraph-based chunks.
    Maintains a sliding window with overlap to preserve context across boundaries.
    """
    chunks: list[TextChunk] = []
    chunk_idx = 0

    for region in regions:
        # Check if the region has text content
        if getattr(region, "region_type", None) != "text":
            continue
        content = getattr(region, "content", "")
        if not content or not isinstance(content, str):
            continue

        page_number = getattr(region, "page_number", 1)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        current_chunk: list[str] = []
        current_length = 0

        for para in paragraphs:
            # If a single paragraph is too large, split by sentences
            if len(para) > max_chunk_char_length:
                # Basic sentence splitter
                sentences = [
                    s.strip()
                    for s in para.replace(". ", ".|").replace("? ", "?|").replace("! ", "!|").split("|")
                    if s.strip()
                ]
                for sentence in sentences:
                    if current_length + len(sentence) > max_chunk_char_length and current_chunk:
                        chunks.append(
                            TextChunk(
                                chunk_id=f"{document_id}_ch_{chunk_idx}",
                                document_id=document_id,
                                page_number=page_number,
                                text=" ".join(current_chunk),
                            )
                        )
                        chunk_idx += 1
                        # Overlap: keep the last sentence
                        current_chunk = [current_chunk[-1]] if current_chunk else []
                        current_length = sum(len(s) for s in current_chunk)

                    current_chunk.append(sentence)
                    current_length += len(sentence)
            else:
                if current_length + len(para) > max_chunk_char_length and current_chunk:
                    chunks.append(
                        TextChunk(
                            chunk_id=f"{document_id}_ch_{chunk_idx}",
                            document_id=document_id,
                            page_number=page_number,
                            text="\n\n".join(current_chunk),
                        )
                    )
                    chunk_idx += 1
                    # Overlap: keep the last N paragraphs
                    current_chunk = current_chunk[-overlap_paragraphs:] if overlap_paragraphs > 0 else []
                    current_length = sum(len(p) for p in current_chunk)

                current_chunk.append(para)
                current_length += len(para)

        if current_chunk:
            chunks.append(
                TextChunk(
                    chunk_id=f"{document_id}_ch_{chunk_idx}",
                    document_id=document_id,
                    page_number=page_number,
                    text="\n\n".join(current_chunk),
                )
            )
            chunk_idx += 1

    return chunks


