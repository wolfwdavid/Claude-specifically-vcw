"""E4/E5 stage 2: score offline agent selections against the manifest.

Input: a shortlist directory produced by ``export_shortlists.py`` (contains
``manifest.json``) and a selections JSONL with one row per task:

    {"task_id": <int>, "tool_id": <int>, "confidence": <float>, "reason": "..."}

Reports:
  - end-to-end accuracy (selected == gold) with a bootstrap 95% CI
  - retrieval ceiling (gold-in-shortlist rate) for context
  - E5 (if the manifest has stripped tasks): abstention precision/recall,
    where abstention = tool_id == -1 and a stripped task is a positive.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def bootstrap_ci(flags: list[bool], n_boot: int = 10_000, seed: int = 257) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(flags)
    means = []
    for _ in range(n_boot):
        s = sum(flags[rng.randrange(n)] for _ in range(n))
        means.append(s / n)
    means.sort()
    return means[int(0.025 * n_boot)], means[int(0.975 * n_boot)]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--shortlists", required=True, help="dir containing manifest.json")
    p.add_argument("--selections", required=True, help="JSONL of model selections")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    manifest = json.loads((Path(args.shortlists) / "manifest.json").read_text(encoding="utf-8"))
    tasks = {t["task_id"]: t for t in manifest["tasks"]}

    selections: dict[int, dict] = {}
    with Path(args.selections).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            selections[int(row["task_id"])] = row

    missing = sorted(set(tasks) - set(selections))
    if missing:
        print(f"WARNING: {len(missing)} tasks lack selections: {missing[:10]}...")

    live = {tid: t for tid, t in tasks.items() if not t["gold_stripped"]}
    flags = []
    for tid, t in sorted(live.items()):
        sel = selections.get(tid, {"tool_id": -1})
        flags.append(int(sel["tool_id"]) == t["gold_tool_id"])
    acc = sum(flags) / len(flags) if flags else 0.0
    lo, hi = bootstrap_ci(flags) if flags else (0.0, 0.0)
    ceiling = sum(1 for t in live.values() if t["gold_in_shortlist"]) / len(live) if live else 0.0

    summary = {
        "retriever": manifest["retriever"],
        "k": manifest["k"],
        "n_tasks_scored": len(flags),
        "agent_accuracy": round(acc, 4),
        "accuracy_ci95": [round(lo, 4), round(hi, 4)],
        "gold_in_shortlist_rate": round(ceiling, 4),
    }

    stripped = {tid: t for tid, t in tasks.items() if t["gold_stripped"]}
    if stripped:
        abstained = {tid for tid, s in selections.items() if int(s["tool_id"]) == -1}
        tp = len(abstained & set(stripped))
        fp = len(abstained - set(stripped))
        fn = len(set(stripped) - abstained)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        summary["abstention"] = {
            "n_stripped": len(stripped),
            "n_abstained": len(abstained),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
        }

    print(json.dumps(summary, indent=2))
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
