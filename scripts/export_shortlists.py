"""E4/E5 stage 1: export retriever shortlists as batched selection jobs.

The live ``trbench agent`` loop needs a chat-API backend. When no backend
is available, this script decouples retrieval from selection: it runs the
retriever over every task and writes the top-k candidate shortlists to
batch files that any model session can process offline. Selections come
back as JSONL ({"task_id": ..., "tool_id": ..., "confidence": ...,
"reason": ...}) and are scored by ``score_agent_runs.py``.

Gold tool IDs are withheld from the batch files (they live in the manifest)
so the selection model cannot be leaked the answer.

E5 support: ``--strip-golds FRAC`` removes FRAC of the gold tools from the
registry before retrieval (seeded, reproducible). On those tasks the
correct behaviour is abstention (tool_id = -1). The manifest records which
tasks were stripped.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tool_retrieval_100k.benchmark import filter_to_registry, load_tasks
from tool_retrieval_100k.registry import Registry
from tool_retrieval_100k.retrievers import BM25Retriever, DenseRetriever, HierarchicalRetriever

SEED = 257


def build_retriever(name: str, reg: Registry, dense: DenseRetriever | None = None):
    if name == "bm25":
        r = BM25Retriever(reg)
    elif name == "dense":
        r = dense or DenseRetriever(reg)
    elif name == "hierarchical":
        r = HierarchicalRetriever(reg, dense=dense)
    else:
        raise SystemExit(f"unknown retriever {name}")
    r.index()
    return r


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", default="data/registry.jsonl")
    p.add_argument("--tasks", default="data/tasks.jsonl")
    p.add_argument("--retriever", required=True, choices=["bm25", "dense", "hierarchical"])
    p.add_argument("--k", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=25)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--strip-golds", type=float, default=0.0, help="E5: fraction of gold tools removed from registry")
    args = p.parse_args()

    reg = Registry.from_jsonl(args.registry)
    raw = load_tasks(args.tasks)
    tasks = filter_to_registry(raw, reg)

    stripped_ids: set[int] = set()
    if args.strip_golds > 0:
        rng = random.Random(SEED)
        golds = sorted({t.gold_tool_id for t in tasks})
        n_strip = int(len(golds) * args.strip_golds)
        stripped_ids = set(rng.sample(golds, n_strip))
        reg = Registry(t for t in reg if t.tool_id not in stripped_ids)
        print(f"stripped {len(stripped_ids)} gold tools; registry now {len(reg)}")

    # Hierarchical/dense share one dense index; keep cache dir stable.
    dense = DenseRetriever(reg) if args.retriever in ("dense", "hierarchical") else None
    r = build_retriever(args.retriever, reg, dense=dense)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    manifest = []
    batch: list[dict] = []
    batch_idx = 0

    def flush() -> None:
        nonlocal batch, batch_idx
        if not batch:
            return
        (out / f"batch_{batch_idx:03d}.json").write_text(
            json.dumps({"batch": batch_idx, "items": batch}, indent=1), encoding="utf-8"
        )
        batch = []
        batch_idx += 1

    for i, t in enumerate(tasks):
        hits = r.search(t.query, k=args.k)
        candidates = [
            {"tool_id": h.tool.tool_id, "name": h.tool.name}
            for h in hits
        ]
        manifest.append(
            {
                "task_id": i,
                "query": t.query,
                "gold_tool_id": t.gold_tool_id,
                "gold_stripped": t.gold_tool_id in stripped_ids,
                "gold_in_shortlist": any(c["tool_id"] == t.gold_tool_id for c in candidates),
            }
        )
        batch.append({"task_id": i, "query": t.query, "candidates": candidates})
        if len(batch) >= args.batch_size:
            flush()
    flush()

    (out / "manifest.json").write_text(
        json.dumps(
            {
                "retriever": args.retriever,
                "k": args.k,
                "registry_size": len(reg),
                "n_tasks": len(manifest),
                "strip_golds": args.strip_golds,
                "tasks": manifest,
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    in_short = sum(1 for m in manifest if m["gold_in_shortlist"])
    print(f"{args.retriever} k={args.k}: {batch_idx} batches, gold-in-shortlist {in_short}/{len(manifest)}")


if __name__ == "__main__":
    main()
