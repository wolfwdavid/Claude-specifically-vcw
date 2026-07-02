"""E3 retrieval sweep (see NEXT_EXPERIMENTS.md).

Runs all three retrievers over the E2 benchmark at k in {5, 10, 20, 50},
plus the hierarchical bucket_top_n sweep in {1, 3, 5, 10}. Builds each
retriever once in-process so the dense embedding matrix is computed a
single time and shared (DenseRetriever caches to data/cache/).

Also accounts the *embeddings read per query* for each retriever:
  bm25          -> 0 (lexical)
  dense         -> full corpus size
  hierarchical  -> centroid count + sum of the top-N buckets' populations,
                   averaged over queries (bucket choice is query-dependent)

Writes one JSON per configuration to results/, plus a consolidated
results/e3_summary.json used to fill RESEARCH_NOTE.md table 3.1.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tool_retrieval_100k.benchmark import filter_to_registry, load_tasks
from tool_retrieval_100k.metrics import score
from tool_retrieval_100k.registry import Registry
from tool_retrieval_100k.retrievers import BM25Retriever, DenseRetriever, HierarchicalRetriever

K_SWEEP = [5, 10, 20, 50]
BUCKET_TOP_N_SWEEP = [1, 3, 5, 10]


def hier_embeddings_read(h: HierarchicalRetriever, query: str) -> int:
    """Centroids compared + members of the buckets the query actually opens."""
    model = h._dense._load_model()
    q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)[0]
    bucket_scores = h._centroid_matrix @ q
    top_b = np.argsort(-bucket_scores)[: h.bucket_top_n]
    opened = sum(len(h._bucket_to_indices[h._bucket_ids[bi]]) for bi in top_b)
    return len(h._bucket_ids) + opened


def run(registry_path: str, tasks_path: str, out_dir: str) -> None:
    reg = Registry.from_jsonl(registry_path)
    print(f"loaded {len(reg)} tools", flush=True)

    raw = load_tasks(tasks_path)
    tasks = filter_to_registry(raw, reg)
    print(f"{len(tasks)}/{len(raw)} tasks valid", flush=True)

    dense = DenseRetriever(reg)
    t0 = time.time()
    dense.index()
    print(f"dense index ready in {time.time() - t0:.0f}s", flush=True)
    bm25 = BM25Retriever(reg)
    bm25.index()
    print("bm25 index ready", flush=True)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary: list[dict] = []

    def eval_retriever(name: str, retriever, k: int, extra: dict | None = None) -> dict:
        preds = []
        emb_reads = []
        for t in tasks:
            hits = retriever.search(t.query, k=k)
            preds.append((t.gold_tool_id, hits))
            if name == "hierarchical":
                emb_reads.append(hier_embeddings_read(retriever, t.query))
        s = score(preds).as_dict()
        row = {"retriever": name, "k": k, **(extra or {}), "metrics": s}
        if name == "bm25":
            row["embeddings_read_per_query"] = 0
        elif name == "dense":
            row["embeddings_read_per_query"] = len(reg)
        else:
            row["embeddings_read_per_query"] = round(float(np.mean(emb_reads)), 1)
        return row

    for k in K_SWEEP:
        for name, r in [("bm25", bm25), ("dense", dense)]:
            row = eval_retriever(name, r, k)
            summary.append(row)
            tag = f"e3_{name}_k{k}"
            (out / f"{tag}.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
            print(f"{tag}: {row['metrics']}", flush=True)

    for top_n in BUCKET_TOP_N_SWEEP:
        h = HierarchicalRetriever(reg, dense=dense, bucket_top_n=top_n)
        h.index()
        for k in K_SWEEP:
            row = eval_retriever("hierarchical", h, k, extra={"bucket_top_n": top_n})
            summary.append(row)
            tag = f"e3_hier_n{top_n}_k{k}"
            (out / f"{tag}.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
            print(f"{tag}: {row['metrics']} emb_read={row['embeddings_read_per_query']}", flush=True)

    (out / "e3_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {len(summary)} rows -> {out / 'e3_summary.json'}", flush=True)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", default="data/registry.jsonl")
    p.add_argument("--tasks", default="data/tasks.jsonl")
    p.add_argument("--out", default="results")
    a = p.parse_args()
    run(a.registry, a.tasks, a.out)
