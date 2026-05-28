"""CLI entry point: ``a11yeval-compare``.

Examples:

    # Two targets, Claude as judge
    a11yeval-compare \\
        --target anthropic:claude-sonnet-4-6 \\
        --target groq:llama-3.1-70b-versatile \\
        --judge anthropic:claude-sonnet-4-6 \\
        --out-json results/cmp.json --out-md results/cmp.md

    # Three free-tier targets, Gemini judge
    a11yeval-compare \\
        --target ollama:llama3.1:70b \\
        --target groq:llama-3.1-70b-versatile \\
        --target gemini:gemini-2.0-flash \\
        --judge gemini:gemini-2.0-flash
"""

from __future__ import annotations

import click

from .compare import compare_models
from .dimensions import ALL_DIMENSIONS


_DIM_BY_NAME = {d.name: d for d in ALL_DIMENSIONS}


@click.command()
@click.option("--target", "targets", multiple=True, required=True, help="Backend spec; pass multiple times.")
@click.option("--judge", default="anthropic:claude-sonnet-4-6", help="Backend spec for the judge (held fixed across targets).")
@click.option("--only", default=None, help="Comma-separated dimension names. Default: all.")
@click.option("--out-json", default=None, help="Path for the structured JSON report.")
@click.option("--out-md", default=None, help="Path for the markdown comparison table.")
def main(targets: tuple[str, ...], judge: str, only: str | None, out_json: str | None, out_md: str | None) -> None:
    """Run the a11y eval across multiple target models with a shared judge."""
    if only:
        wanted = [n.strip() for n in only.split(",") if n.strip()]
        try:
            dims = [_DIM_BY_NAME[n] for n in wanted]
        except KeyError as e:
            raise click.BadParameter(f"unknown dimension: {e.args[0]}")
    else:
        dims = ALL_DIMENSIONS

    compare_models(
        targets=list(targets),
        judge=judge,
        dimensions=dims,
        out_json=out_json,
        out_md=out_md,
    )


if __name__ == "__main__":
    main()
