"""CLI entry point: `a11yeval`.

The --target and --judge flags accept backend spec strings:
    anthropic:claude-sonnet-4-6      (default; needs ANTHROPIC_API_KEY)
    ollama:llama3.1:70b               (free, local; needs Ollama running)
    gemini:gemini-2.0-flash           (free tier; needs GOOGLE_API_KEY)
    groq:llama-3.1-70b-versatile      (free tier; needs GROQ_API_KEY)
"""

from __future__ import annotations

import click

from .dimensions import ALL_DIMENSIONS
from .runner import run_all


_DIM_BY_NAME = {d.name: d for d in ALL_DIMENSIONS}


@click.command()
@click.option("--target", default="anthropic:claude-sonnet-4-6", help="Backend spec for the model under test.")
@click.option("--judge", default="anthropic:claude-sonnet-4-6", help="Backend spec for the judge.")
@click.option(
    "--only",
    default=None,
    help=f"Comma-separated dimension names. Default: all of {sorted(_DIM_BY_NAME)}.",
)
@click.option("--out", default=None, help="JSON output path.")
def main(target: str, judge: str, only: str | None, out: str | None) -> None:
    """Run the Cowork Accessibility Eval Pack."""
    if only:
        wanted = [n.strip() for n in only.split(",") if n.strip()]
        try:
            dims = [_DIM_BY_NAME[n] for n in wanted]
        except KeyError as e:
            raise click.BadParameter(f"unknown dimension: {e.args[0]}")
    else:
        dims = ALL_DIMENSIONS
    run_all(target=target, judge=judge, dimensions=dims, out_path=out)


if __name__ == "__main__":
    main()
