"""Hierarchical taxonomy-walk retrieval.

A 100K-entry flat catalog ignores the structure most real tool registries
have: namespaces, categories, capability clusters. This retriever exploits
that structure by walking the implied taxonomy in two stages:

  1. Cluster discovery — group tools by ID-prefix bucket (a proxy for the
     namespace they were generated under) and pick the top-N buckets via
     cosine similarity between the query and each bucket's centroid.
  2. Within-bucket dense rerank — only embed and score tools inside the
     surviving buckets.

The hypothesis under test: hierarchical narrowing recovers most of the
quality of full-catalog dense retrieval while reading a small fraction of
the embeddings, which is the regime Cowork agents actually live in.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from ..registry import Registry
from .base import Hit, Retriever
from .dense import DenseRetriever


def _bucket_of(tool_id: int) -> int:
    """Coarse top-level bucket: powers of 10 group id-ranges.

    0–9 → 0, 10–99 → 1, 100–999 → 2, etc. The intuition is that a tool
    generator emitting ids 12, 117, 10148 produces semantic clusters at
    each decade. Real registries should swap this for an actual namespace
    field.
    """
    if tool_id <= 0:
        return 0
    n = 0
    v = tool_id
    while v >= 10:
        v //= 10
        n += 1
    return n


class HierarchicalRetriever(Retriever):
    name = "hierarchical"

    def __init__(
        self,
        registry: Registry,
        dense: DenseRetriever | None = None,
        bucket_top_n: int = 3,
        within_bucket_k: int = 50,
    ):
        super().__init__(registry)
        self._dense = dense or DenseRetriever(registry)
        self.bucket_top_n = bucket_top_n
        self.within_bucket_k = within_bucket_k
        self._tools = list(registry)
        self._bucket_to_indices: dict[int, list[int]] = defaultdict(list)
        self._bucket_centroids: dict[int, np.ndarray] = {}
        self._bucket_ids: list[int] = []
        self._centroid_matrix: np.ndarray | None = None

    def index(self) -> None:
        self._dense.index()
        if self._centroid_matrix is not None:
            return
        emb = self._dense._embeddings
        assert emb is not None
        for i, t in enumerate(self._tools):
            self._bucket_to_indices[_bucket_of(t.tool_id)].append(i)
        self._bucket_ids = sorted(self._bucket_to_indices)
        centroids = []
        for b in self._bucket_ids:
            idxs = self._bucket_to_indices[b]
            c = emb[idxs].mean(axis=0)
            c /= max(np.linalg.norm(c), 1e-12)
            self._bucket_centroids[b] = c
            centroids.append(c)
        self._centroid_matrix = np.stack(centroids, axis=0)

    def search(self, query: str, k: int = 10) -> list[Hit]:
        assert self._centroid_matrix is not None, "call index() before search()"
        model = self._dense._load_model()
        q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)[0]

        bucket_scores = self._centroid_matrix @ q
        top_b = np.argsort(-bucket_scores)[: self.bucket_top_n]
        candidate_idxs: list[int] = []
        for bi in top_b:
            candidate_idxs.extend(self._bucket_to_indices[self._bucket_ids[bi]])

        if not candidate_idxs:
            return []

        emb = self._dense._embeddings
        assert emb is not None
        sub = emb[candidate_idxs]
        scores = sub @ q
        order = np.argsort(-scores)[:k]
        return [
            Hit(tool=self._tools[candidate_idxs[i]], score=float(scores[i]))
            for i in order
        ]
