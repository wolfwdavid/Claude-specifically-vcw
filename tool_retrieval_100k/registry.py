"""Load a large tool registry from disk into an in-memory catalog.

A registry is a directory whose immediate children are tool packages. Each
child directory name is parsed as ``<id>_<slug>``; the slug provides the
human-readable surface that retrievers index against.

The loader is deliberately tolerant: it does not import the tool code, only
inspects directory names and optional ``description`` metadata if present.
This keeps registry loading cheap (a few seconds for ~100K entries) and
decouples retrieval research from the tools' runtime dependencies.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

_NAME_RE = re.compile(r"^(?P<id>\d+)_(?P<slug>.+)$")


@dataclass(frozen=True)
class Tool:
    tool_id: int
    slug: str
    name: str
    description: str
    path: Path

    @property
    def search_text(self) -> str:
        """Concatenation used by lexical and dense retrievers."""
        return f"{self.name}. {self.description}".strip()


def _slug_to_name(slug: str) -> str:
    return slug.replace("_", " ").strip().title()


def _read_description(tool_dir: Path) -> str:
    """Best-effort description: __init__.py docstring or DESCRIPTION.md."""
    desc_file = tool_dir / "DESCRIPTION.md"
    if desc_file.is_file():
        return desc_file.read_text(encoding="utf-8", errors="ignore").strip()

    init = tool_dir / "__init__.py"
    if init.is_file():
        text = init.read_text(encoding="utf-8", errors="ignore")
        m = re.match(r'\s*"""([^"]+)"""', text, flags=re.DOTALL)
        if m:
            return m.group(1).strip()
    return ""


def iter_tools(root: Path) -> Iterator[Tool]:
    """Yield Tool objects for every well-formed child directory of ``root``."""
    root = Path(root)
    if not root.is_dir():
        raise FileNotFoundError(f"Registry root does not exist: {root}")

    for child in root.iterdir():
        if not child.is_dir():
            continue
        if child.name.startswith((".", "_")):
            continue
        m = _NAME_RE.match(child.name)
        if not m:
            continue
        tool_id = int(m.group("id"))
        slug = m.group("slug")
        yield Tool(
            tool_id=tool_id,
            slug=slug,
            name=_slug_to_name(slug),
            description=_read_description(child),
            path=child,
        )


class Registry:
    """In-memory tool catalog with O(1) lookup by ID and by directory name."""

    def __init__(self, tools: Iterable[Tool]):
        self._tools: list[Tool] = list(tools)
        self._by_id: dict[int, Tool] = {t.tool_id: t for t in self._tools}
        self._by_slug: dict[str, Tool] = {t.slug: t for t in self._tools}

    @classmethod
    def from_directory(cls, root: str | Path) -> "Registry":
        return cls(iter_tools(Path(root)))

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "Registry":
        """Load a pre-exported registry (one JSON object per line)."""
        tools: list[Tool] = []
        with Path(path).open("r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                tools.append(
                    Tool(
                        tool_id=int(obj["tool_id"]),
                        slug=obj["slug"],
                        name=obj.get("name") or _slug_to_name(obj["slug"]),
                        description=obj.get("description", ""),
                        path=Path(obj.get("path", "")),
                    )
                )
        return cls(tools)

    def __len__(self) -> int:
        return len(self._tools)

    def __iter__(self) -> Iterator[Tool]:
        return iter(self._tools)

    def by_id(self, tool_id: int) -> Tool:
        return self._by_id[tool_id]

    def by_slug(self, slug: str) -> Tool:
        return self._by_slug[slug]

    def export_jsonl(self, path: str | Path) -> None:
        with Path(path).open("w", encoding="utf-8") as f:
            for t in self._tools:
                f.write(
                    json.dumps(
                        {
                            "tool_id": t.tool_id,
                            "slug": t.slug,
                            "name": t.name,
                            "description": t.description,
                            "path": str(t.path),
                        }
                    )
                    + "\n"
                )
