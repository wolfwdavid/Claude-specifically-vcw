"""Sparse lexical retrieval baseline (BM25).

Tokenizes on non-alphanumeric boundaries and lowercases. Indexes ``Tool.
search_text``. This is the classical baseline that any dense or structured
method has to beat to be interesting.
"""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from ..registry import Registry
from .base import Hit, Retriever

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


class BM25Retriever(Retriever):
    name = "bm25"

    def __init__(self, registry: Registry):
        super().__init__(registry)
        self._tools = list(registry)
        self._bm25: BM25Okapi | None = None

    def index(self) -> None:
        if self._bm25 is not None:
            return
        corpus = [_tokenize(t.search_text) for t in self._tools]
        self._bm25 = BM25Okapi(corpus)

    def search(self, query: str, k: int = 10) -> list[Hit]:
        assert self._bm25 is not None, "call index() before search()"
        tokens = _tokenize(query)
        scores = self._bm25.get_scores(tokens)
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [Hit(tool=self._tools[i], score=float(scores[i])) for i in top_idx]
