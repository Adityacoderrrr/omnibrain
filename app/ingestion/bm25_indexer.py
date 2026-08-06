"""
BM25 Keyword Indexer for Hybrid RAG Retrieval.
Provides fast sparse keyword search over document chunks to complement vector semantic search.
"""

import re
import math
from typing import List, Dict, Any, Tuple


class BM25Indexer:
    """
    In-memory BM25 Okapi search engine.
    Indexes text chunks with term frequencies and document frequencies for fast keyword retrieval.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_chunks: Dict[str, Dict[str, Any]] = {}  # chunk_id -> payload dict
        self.doc_lengths: Dict[str, int] = {}             # chunk_id -> token count
        self.doc_tf: Dict[str, Dict[str, int]] = {}       # chunk_id -> {term -> count}
        self.df: Dict[str, int] = {}                       # term -> document count
        self.avg_doc_len: float = 0.0
        self.total_docs: int = 0

    def _tokenize(self, text: str) -> List[str]:
        """Convert text into lowercase tokens."""
        return [word.lower() for word in re.findall(r'\b\w+\b', text or "")]

    def add_chunks(self, chunks: List[Any], filename: str = "", tags: List[str] = None, collection: str = "") -> None:
        """
        Index a list of TextChunk objects into BM25.
        """
        for chunk in chunks:
            chunk_id = getattr(chunk, "chunk_id", str(id(chunk)))
            doc_id = getattr(chunk, "document_id", "")
            page_num = getattr(chunk, "page_number", 1)
            text = getattr(chunk, "text", "")

            tokens = self._tokenize(text)
            if not tokens:
                continue

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1

            self.doc_chunks[chunk_id] = {
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "filename": filename or doc_id,
                "page_number": page_num,
                "text": text,
                "tags": tags or [],
                "collection": collection or "default",
            }
            self.doc_lengths[chunk_id] = len(tokens)
            self.doc_tf[chunk_id] = tf

            for term in tf:
                self.df[term] = self.df.get(term, 0) + 1

        self.total_docs = len(self.doc_chunks)
        if self.total_docs > 0:
            self.avg_doc_len = sum(self.doc_lengths.values()) / self.total_docs

    def remove_document(self, document_id: str) -> None:
        """Remove all chunks associated with a document_id."""
        to_remove = [cid for cid, meta in self.doc_chunks.items() if meta.get("document_id") == document_id]
        for cid in to_remove:
            tf = self.doc_tf.get(cid, {})
            for term in tf:
                if term in self.df:
                    self.df[term] -= 1
                    if self.df[term] <= 0:
                        del self.df[term]
            self.doc_chunks.pop(cid, None)
            self.doc_lengths.pop(cid, None)
            self.doc_tf.pop(cid, None)

        self.total_docs = len(self.doc_chunks)
        if self.total_docs > 0:
            self.avg_doc_len = sum(self.doc_lengths.values()) / self.total_docs
        else:
            self.avg_doc_len = 0.0

    def search(self, query: str, document_id: str = None, document_ids: List[str] = None, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform BM25 search over indexed chunks.
        Optionally filter by document_id or list of document_ids.
        Returns list of (payload, bm25_score).
        """
        if self.total_docs == 0:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        target_doc_set = None
        if document_ids:
            target_doc_set = set(document_ids)
        elif document_id:
            target_doc_set = {document_id}

        scores: Dict[str, float] = {}

        for token in query_tokens:
            if token not in self.df:
                continue

            n_q = self.df[token]
            idf = math.log((self.total_docs - n_q + 0.5) / (n_q + 0.5) + 1.0)

            for cid, tf_dict in self.doc_tf.items():
                if target_doc_set:
                    doc_id_of_chunk = self.doc_chunks[cid].get("document_id")
                    if doc_id_of_chunk not in target_doc_set:
                        continue

                f_q = tf_dict.get(token, 0)
                if f_q == 0:
                    continue

                doc_len = self.doc_lengths[cid]
                denom = f_q + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                score = idf * (f_q * (self.k1 + 1.0)) / denom
                scores[cid] = scores.get(cid, 0.0) + score

        sorted_cids = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for cid, score in sorted_cids:
            results.append((self.doc_chunks[cid], score))

        return results


# Global BM25 Singleton Instance
bm25_indexer = BM25Indexer()
