"""Multi-target model comparison runner.

Run the full a11y eval against several target backends with the same judge,
emit a comparison table (JSON + markdown). Holding the judge fixed across
targets is what makes the cross-model numbers honest; switching it midway
adds a confound nobody can reason about afterward.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import asdict
from pathlib import Path

from .dimensions import ALL_DIMENSIONS, Dimension


# Special-cased aggregate rows that some dimensions emit beyond pass_rate.
_REFUSAL_PARITY_GAP_ROW = "refusal_parity (mean gap, lower=better)"


def _short_label(spec: str) -> str:
    """Compact column label for spec strings like ``anthropic:claude-sonnet-4-6``."""
    if ":" not in spec:
        return spec
    head, _, tail = spec.partition(":")
    short_model = tail.split("/")[-1]
    return f"{short_model} ({head})"


def compare_models(
    targets: list[str],
    judge: str = "anthropic:claude-sonnet-4-6",
    dimensions: list[type[Dimension]] | None = None,
    out_json: str | Path | None = None,
    out_md: str | Path | None = None,
) -> dict:
    """Run each target through every dimension; return the structured table."""
    dimensions = dimensions or ALL_DIMENSIONS

    # per_target[target_spec][dimension_name] = {"pass_rate": float, "mean_score": float, "extra": {...}}
    per_target: dict[str, dict[str, dict]] = {}

    for target in targets:
        print(f"\n=== {target} (judge: {judge}) ===")
        per_target[target] = {}
        for dim_cls in dimensions:
            try:
                dim = dim_cls(target=target, judge=judge)
            except TypeError:
                dim = dim_cls(target=target)
            s = dim.run()
            extra: dict = {}
            if s.name == "refusal_parity":
                # Pull the aggregate row that RefusalParity appends.
                for r in s.results:
                    if r.case_id == "__aggregate__":
                        extra = {
                            "mean_parity_gap": r.extra.get("mean_parity_gap"),
                            "regressive_pairs": r.extra.get("regressive_pairs"),
                            "n_pairs": r.extra.get("n_pairs"),
                        }
                        break
            per_target[target][s.name] = {
                "pass_rate": round(s.pass_rate, 4),
                "mean_score": round(s.mean_score, 4),
                "n_cases": s.n_cases,
                "extra": extra,
                "results": [asdict(r) for r in s.results],
            }
            print(
                f"  [{s.name}] pass_rate={s.pass_rate:.2%}  mean_score={s.mean_score:.3f}"
            )

    payload = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "judge": judge,
        "targets": targets,
        "per_target": per_target,
    }

    if out_json is not None:
        Path(out_json).parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    if out_md is not None:
        md = render_markdown(payload)
        Path(out_md).parent.mkdir(parents=True, exist_ok=True)
        Path(out_md).write_text(md, encoding="utf-8")

    return payload


def render_markdown(payload: dict) -> str:
    """Render the comparison payload as a markdown table.

    Bold the best score per row across targets. Includes a special row for
    the refusal_parity mean gap (lower is better, so the bolding inverts).
    """
    targets: list[str] = payload["targets"]
    per_target: dict[str, dict[str, dict]] = payload["per_target"]
    if not targets:
        return "_no targets_\n"

    # Collect every dimension name that appeared (preserve first-seen order).
    seen: list[str] = []
    for tgt in targets:
        for name in per_target.get(tgt, {}):
            if name not in seen:
                seen.append(name)

    lines: list[str] = []
    lines.append("# Cowork Accessibility Eval — Model Comparison")
    lines.append("")
    lines.append(f"- Judge: `{payload['judge']}`")
    lines.append(f"- Generated: `{payload['generated_at']}`")
    lines.append(f"- Targets: {len(targets)}")
    lines.append("")
    lines.append("Cell value is `pass_rate` (per-dimension). Bold = best in row.")
    lines.append("")

    header = ["Dimension"] + [_short_label(t) for t in targets]
    sep = ["---"] * len(header)
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(sep) + " |")

    def _fmt(val: float | None, *, lower_better: bool = False, best: bool) -> str:
        if val is None:
            return "—"
        if lower_better:
            txt = f"{val:+.3f}"
        else:
            txt = f"{val:.2%}"
        return f"**{txt}**" if best else txt

    for dim_name in seen:
        row_vals = [per_target[t].get(dim_name, {}).get("pass_rate") for t in targets]
        best_val = max((v for v in row_vals if v is not None), default=None)
        cells = [
            _fmt(v, best=(v is not None and v == best_val)) for v in row_vals
        ]
        lines.append("| " + " | ".join([dim_name, *cells]) + " |")

    # Special row: refusal_parity mean gap (lower better)
    if "refusal_parity" in seen:
        gaps = [
            per_target[t].get("refusal_parity", {}).get("extra", {}).get("mean_parity_gap")
            for t in targets
        ]
        present = [g for g in gaps if g is not None]
        if present:
            best_gap = min(present)
            cells = [
                _fmt(g, lower_better=True, best=(g is not None and g == best_gap))
                for g in gaps
            ]
            lines.append("| " + " | ".join([_REFUSAL_PARITY_GAP_ROW, *cells]) + " |")

    lines.append("")
    lines.append("## How to read this")
    lines.append("")
    lines.append(
        "- `pass_rate` is the fraction of cases where the model met the dimension's pass criterion."
    )
    lines.append(
        "- `refusal_parity (mean gap)` is the average baseline-minus-disability "
        "helpfulness gap across paired prompts. Positive = the model is less helpful on the "
        "disability-flavored prompt. Closer to zero is better."
    )
    lines.append(
        "- Judge is held fixed across all targets, so target-to-target comparisons are "
        "internally consistent. Switching the judge changes absolute numbers but rarely the ranking."
    )
    return "\n".join(lines) + "\n"
