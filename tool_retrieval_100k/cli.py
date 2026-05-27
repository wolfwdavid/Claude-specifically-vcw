"""Command-line entry point for benchmark runs.

Examples:

    # Build a JSONL export of an on-disk registry once, then point the
    # benchmark at it for reproducible runs.
    trbench export-registry --root /path/to/ai_tools --out data/registry.jsonl

    # Retrieval-only benchmark (no Claude calls).
    trbench retrieve --registry data/registry.jsonl --retriever bm25 --k 10

    # Full agent-in-the-loop benchmark.
    trbench agent --registry data/registry.jsonl --retriever hierarchical --k 20 \\
        --tasks data/tasks.jsonl --out results/run_001.json
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import click

from .benchmark import filter_to_registry, load_tasks
from .metrics import score
from .registry import Registry
from .retrievers import BM25Retriever, DenseRetriever, HierarchicalRetriever, Retriever


def _build_retriever(name: str, registry: Registry) -> Retriever:
    name = name.lower()
    if name == "bm25":
        return BM25Retriever(registry)
    if name == "dense":
        return DenseRetriever(registry)
    if name == "hierarchical":
        return HierarchicalRetriever(registry)
    raise click.BadParameter(f"unknown retriever: {name}")


def _load_registry(path: str) -> Registry:
    p = Path(path)
    if p.is_dir():
        return Registry.from_directory(p)
    if p.suffix == ".jsonl":
        return Registry.from_jsonl(p)
    raise click.BadParameter(f"registry path must be a directory or .jsonl: {path}")


@click.group()
def main() -> None:
    """tool-retrieval-100k benchmark CLI."""


@main.command("export-registry")
@click.option("--root", required=True, help="Path to registry root directory.")
@click.option("--out", required=True, help="Output JSONL path.")
def export_registry(root: str, out: str) -> None:
    reg = Registry.from_directory(root)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    reg.export_jsonl(out)
    click.echo(f"exported {len(reg)} tools to {out}")


@main.command("retrieve")
@click.option("--registry", required=True)
@click.option("--retriever", default="bm25", type=click.Choice(["bm25", "dense", "hierarchical"]))
@click.option("--tasks", default=None, help="Optional JSONL of tasks; defaults to the seed set.")
@click.option("--k", default=10, type=int)
@click.option("--out", default=None, help="Optional JSON results path.")
def retrieve_cmd(registry: str, retriever: str, tasks: str | None, k: int, out: str | None) -> None:
    reg = _load_registry(registry)
    click.echo(f"loaded {len(reg)} tools")
    r = _build_retriever(retriever, reg)
    t0 = time.time()
    r.index()
    click.echo(f"indexed in {time.time() - t0:.1f}s")

    raw_tasks = load_tasks(tasks)
    valid = filter_to_registry(raw_tasks, reg)
    click.echo(f"running {len(valid)}/{len(raw_tasks)} tasks (others gold-not-in-registry)")

    predictions = []
    for task in valid:
        hits = r.search(task.query, k=k)
        predictions.append((task.gold_tool_id, hits))

    s = score(predictions)
    click.echo(json.dumps({"retriever": retriever, **s.as_dict()}, indent=2))

    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "retriever": retriever,
                    "k": k,
                    "registry_size": len(reg),
                    "metrics": s.as_dict(),
                    "tasks": [t.as_dict() for t in valid],
                },
                f,
                indent=2,
            )


@main.command("agent")
@click.option("--registry", required=True)
@click.option("--retriever", default="hierarchical", type=click.Choice(["bm25", "dense", "hierarchical"]))
@click.option("--tasks", default=None)
@click.option("--k", default=20, type=int)
@click.option("--model", default="claude-sonnet-4-6")
@click.option("--out", default=None)
def agent_cmd(registry: str, retriever: str, tasks: str | None, k: int, model: str, out: str | None) -> None:
    from .agent import ClaudeAgentRunner

    reg = _load_registry(registry)
    r = _build_retriever(retriever, reg)
    r.index()

    raw_tasks = load_tasks(tasks)
    valid = filter_to_registry(raw_tasks, reg)
    agent = ClaudeAgentRunner(model=model)

    rows = []
    n_correct = 0
    for task in valid:
        hits = r.search(task.query, k=k)
        result = agent.select(task.query, hits)
        correct = result.selected_tool_id == task.gold_tool_id
        n_correct += int(correct)
        rows.append(
            {
                "query": task.query,
                "gold_tool_id": task.gold_tool_id,
                "selected_tool_id": result.selected_tool_id,
                "confidence": result.confidence,
                "correct": correct,
                "reason": result.reason,
                "retrieved_ids": [h.tool.tool_id for h in hits],
            }
        )

    acc = n_correct / len(valid) if valid else 0.0
    summary = {
        "retriever": retriever,
        "model": model,
        "k": k,
        "registry_size": len(reg),
        "n_tasks": len(valid),
        "agent_accuracy": round(acc, 4),
    }
    click.echo(json.dumps(summary, indent=2))

    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "rows": rows}, f, indent=2)


if __name__ == "__main__":
    main()
