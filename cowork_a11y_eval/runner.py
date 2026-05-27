"""Top-level eval runner — execute every dimension, emit a JSON report."""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from pathlib import Path

from .dimensions import ALL_DIMENSIONS, Dimension, DimensionSummary


def run_all(
    target: str = "anthropic:claude-sonnet-4-6",
    judge: str = "anthropic:claude-sonnet-4-6",
    dimensions: list[type[Dimension]] | None = None,
    out_path: str | Path | None = None,
) -> list[DimensionSummary]:
    dimensions = dimensions or ALL_DIMENSIONS
    summaries: list[DimensionSummary] = []
    for dim_cls in dimensions:
        t0 = time.time()
        # Dimensions that take a judge accept it as a kwarg; others ignore it.
        try:
            dim = dim_cls(target=target, judge=judge)
        except TypeError:
            dim = dim_cls(target=target)
        s = dim.run()
        elapsed = time.time() - t0
        print(
            f"[{s.name}] n={s.n_cases}  pass_rate={s.pass_rate:.2%}  "
            f"mean_score={s.mean_score:.3f}  ({elapsed:.1f}s)"
        )
        summaries.append(s)

    if out_path is not None:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "target": target,
                    "judge": judge,
                    "summaries": [
                        {
                            "name": s.name,
                            "n_cases": s.n_cases,
                            "pass_rate": round(s.pass_rate, 4),
                            "mean_score": round(s.mean_score, 4),
                            "results": [asdict(r) for r in s.results],
                        }
                        for s in summaries
                    ],
                },
                f,
                indent=2,
            )
    return summaries
