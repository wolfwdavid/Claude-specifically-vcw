"""Benchmark generation for E2 (see NEXT_EXPERIMENTS.md).

The pipeline has four stages; this script implements the two deterministic
ones. The two model stages run through Claude drafting/review sessions whose
inputs and outputs are plain JSONL files, so the whole pipeline is
reproducible and auditable:

  1. ``sample``   (this script)  — stratified tool sample with sibling context
  2. drafting     (model)        — 2-3 natural queries per sampled tool,
                                   written to ``data/candidates.jsonl``
  3. review       (model)        — every candidate judged for ambiguity
                                   against its sibling tools; verdicts merged
                                   into the candidate rows
  4. ``assemble`` (this script)  — accepted candidates -> ``data/tasks.jsonl``
                                   plus coverage accounting

Sampling is seeded so the tool sample is reproducible. Sibling context
(slugs of the nearest tool IDs) is attached to every sampled tool because
bucket-4 slugs differ only by a role suffix (``..._tracker`` vs
``..._classifier``); a query that does not signal the role is ambiguous by
construction and the reviewer needs the siblings to catch that.
"""

from __future__ import annotations

import argparse
import collections
import json
import random
from pathlib import Path

SEED = 257
# All 9 tools in bucket 0 are used; larger buckets are sampled to keep
# per-bucket query counts balanced (see NEXT_EXPERIMENTS.md stop condition
# and RESEARCH_NOTE.md for the bucket-0 skew note).
BUCKET_TOOL_QUOTA = {0: 9, 1: 40, 2: 40, 3: 40, 4: 40}
QUERIES_PER_TOOL = 3
SIBLING_WINDOW = 6


def bucket_of(tool_id: int) -> int:
    return len(str(tool_id)) - 1


def load_registry(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def cmd_sample(args: argparse.Namespace) -> None:
    rows = load_registry(Path(args.registry))
    by_id = {int(r["tool_id"]): r for r in rows}
    buckets: dict[int, list[dict]] = collections.defaultdict(list)
    for r in rows:
        buckets[bucket_of(int(r["tool_id"]))].append(r)

    rng = random.Random(SEED)
    sampled: list[dict] = []
    for b, quota in BUCKET_TOOL_QUOTA.items():
        pool = sorted(buckets.get(b, []), key=lambda r: int(r["tool_id"]))
        take = pool if len(pool) <= quota else rng.sample(pool, quota)
        for r in sorted(take, key=lambda x: int(x["tool_id"])):
            tid = int(r["tool_id"])
            siblings = [
                by_id[i]["slug"]
                for i in range(tid - SIBLING_WINDOW, tid + SIBLING_WINDOW + 1)
                if i != tid and i in by_id and bucket_of(i) == b
            ]
            sampled.append(
                {
                    "tool_id": tid,
                    "slug": r["slug"],
                    "name": r["name"],
                    "bucket": b,
                    "queries_wanted": QUERIES_PER_TOOL,
                    "sibling_slugs": siblings,
                }
            )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for s in sampled:
            f.write(json.dumps(s) + "\n")
    per_bucket = collections.Counter(s["bucket"] for s in sampled)
    print(f"sampled {len(sampled)} tools -> {out}")
    for b in sorted(per_bucket):
        print(f"  bucket {b}: {per_bucket[b]} tools ({per_bucket[b] * QUERIES_PER_TOOL} queries planned)")


def cmd_assemble(args: argparse.Namespace) -> None:
    candidates = []
    with Path(args.candidates).open("r", encoding="utf-8") as f:
        for line in f:
            candidates.append(json.loads(line))

    accepted = [c for c in candidates if c.get("verdict") == "accept"]
    rejected = [c for c in candidates if c.get("verdict") != "accept"]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for c in accepted:
            f.write(
                json.dumps(
                    {
                        "query": c["query"],
                        "gold_tool_id": int(c["gold_tool_id"]),
                        "source": "e2_generated",
                    }
                )
                + "\n"
            )

    per_bucket = collections.Counter(bucket_of(int(c["gold_tool_id"])) for c in accepted)
    counts = [per_bucket[b] for b in sorted(per_bucket)]
    print(f"assembled {len(accepted)} tasks -> {out}  (rejected {len(rejected)})")
    for b in sorted(per_bucket):
        print(f"  bucket {b}: {per_bucket[b]} tasks")
    if counts and min(counts) > 0:
        print(f"  max:min bucket ratio = {max(counts) / min(counts):.1f}:1")
    reasons = collections.Counter(c.get("reject_reason", "?") for c in rejected)
    for reason, n in reasons.most_common():
        print(f"  rejected [{reason}]: {n}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("sample", help="stratified tool sample with sibling context")
    ps.add_argument("--registry", default="data/registry.jsonl")
    ps.add_argument("--out", default="data/sample_tools.jsonl")
    ps.set_defaults(func=cmd_sample)

    pa = sub.add_parser("assemble", help="accepted candidates -> tasks.jsonl")
    pa.add_argument("--candidates", default="data/candidates.jsonl")
    pa.add_argument("--out", default="data/tasks.jsonl")
    pa.set_defaults(func=cmd_assemble)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
