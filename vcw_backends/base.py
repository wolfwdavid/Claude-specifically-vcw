"""Backend protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BackendError(RuntimeError):
    pass


class Backend(ABC):
    name: str = "base"

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def chat(self, system: str, user: str, max_tokens: int = 800) -> str:
        """Return the model's text response."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model!r}>"
