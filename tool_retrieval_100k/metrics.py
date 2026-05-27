"""Retrieval metrics."""

from __future__ import annotations

from dataclasses import dataclass

from .retrievers.base import Hit


@dataclass
class RetrievalScore:
    n: int
    recall_at_1: float
    recall_at_5: float
    recall_at_10: float
    mrr: float

    def as_dict(self) -> dict:
        return {
            "n": self.n,
            "recall@1": round(self.recall_at_1, 4),
            "recall@5": round(self.recall_at_5, 4),
            "recall@10": round(self.recall_at_10, 4),
            "mrr": round(self.mrr, 4),
        }


def _rank_of_gold(hits: list[Hit], gold_id: int) -> int | None:
    for r, h in enumerate(hits, start=1):
        if h.tool.tool_id == gold_id:
            return r
    return None


def score(predictions: list[tuple[int, list[Hit]]]) -> RetrievalScore:
    """``predictions`` is a list of (gold_tool_id, ranked_hits)."""
    n = len(predictions)
    if n == 0:
        return RetrievalScore(0, 0.0, 0.0, 0.0, 0.0)
    r1 = r5 = r10 = 0
    mrr_sum = 0.0
    for gold, hits in predictions:
        rank = _rank_of_gold(hits, gold)
        if rank is None:
            continue
        if rank == 1:
            r1 += 1
        if rank <= 5:
            r5 += 1
        if rank <= 10:
            r10 += 1
        mrr_sum += 1.0 / rank
    return RetrievalScore(
        n=n,
        recall_at_1=r1 / n,
        recall_at_5=r5 / n,
        recall_at_10=r10 / n,
        mrr=mrr_sum / n,
    )
