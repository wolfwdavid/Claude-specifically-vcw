"""Retriever interface.

A retriever maps a natural-language ``query`` to a ranked list of ``Hit``s
drawn from the registry. The interface is deliberately minimal so that
lexical, dense, and structured strategies can be compared head-to-head on
the same eval harness.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..registry import Registry, Tool


@dataclass(frozen=True)
class Hit:
    tool: Tool
    score: float


class Retriever(ABC):
    name: str = "base"

    def __init__(self, registry: Registry):
        self.registry = registry

    @abstractmethod
    def index(self) -> None:
        """Build any internal data structures. Idempotent."""

    @abstractmethod
    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Return the top-``k`` hits for ``query``, highest score first."""
