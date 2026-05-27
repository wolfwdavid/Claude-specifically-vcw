"""Dense embedding retrieval.

Embeds every tool's ``search_text`` once with a sentence-transformer model,
caches the matrix to ``data/cache/<model>.npy``, then ranks queries by cosine
similarity. The 100K-scale matmul is small enough to run on a single GPU or
even CPU in a few seconds per query, which is the point: dense retrieval at
this scale is not the bottleneck — picking the right answer from the top-k is.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from ..registry import Registry
from .base import Hit, Retriever

_DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _l2_normalize(x: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.clip(norm, 1e-12, None)


class DenseRetriever(Retriever):
    name = "dense"

    def __init__(
        self,
        registry: Registry,
        model_name: str = _DEFAULT_MODEL,
        cache_dir: str | Path = "data/cache",
        batch_size: int = 256,
    ):
        super().__init__(registry)
        self._tools = list(registry)
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.batch_size = batch_size
        self._embeddings: np.ndarray | None = None
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _cache_path(self) -> Path:
        key = hashlib.sha1(
            f"{self.model_name}|{len(self._tools)}|{self._tools[0].slug if self._tools else ''}".encode()
        ).hexdigest()[:12]
        slug = self.model_name.replace("/", "_")
        return self.cache_dir / f"dense_{slug}_{key}.npy"

    def index(self) -> None:
        if self._embeddings is not None:
            return
        cache = self._cache_path()
        if cache.is_file():
            self._embeddings = np.load(cache)
            return

        model = self._load_model()
        texts = [t.search_text for t in self._tools]
        emb = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        np.save(cache, emb)
        self._embeddings = emb

    def search(self, query: str, k: int = 10) -> list[Hit]:
        assert self._embeddings is not None, "call index() before search()"
        model = self._load_model()
        q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)[0]
        scores = self._embeddings @ q
        top_idx = np.argpartition(-scores, min(k, len(scores) - 1))[:k]
        top_idx = top_idx[np.argsort(-scores[top_idx])]
        return [Hit(tool=self._tools[i], score=float(scores[i])) for i in top_idx]
