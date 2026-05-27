"""CLI entry point: `a11yeval`."""

from __future__ import annotations

import click

from .dimensions import ALL_DIMENSIONS
from .runner import run_all


_DIM_BY_NAME = {d.name: d for d in ALL_DIMENSIONS}


@click.command()
@click.option("--model", default="claude-sonnet-4-6", help="Model under test.")
@click.option(
    "--only",
    default=None,
    help=f"Comma-separated dimension names. Default: all of {sorted(_DIM_BY_NAME)}.",
)
@click.option("--out", default=None, help="JSON output path.")
def main(model: str, only: str | None, out: str | None) -> None:
    """Run the Cowork Accessibility Eval Pack."""
    if only:
        wanted = [n.strip() for n in only.split(",") if n.strip()]
        try:
            dims = [_DIM_BY_NAME[n] for n in wanted]
        except KeyError as e:
            raise click.BadParameter(f"unknown dimension: {e.args[0]}")
    else:
        dims = ALL_DIMENSIONS
    run_all(target_model=model, dimensions=dims, out_path=out)


if __name__ == "__main__":
    main()
