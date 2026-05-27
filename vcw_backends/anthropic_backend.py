"""Anthropic backend (paid, with $5 free credit on new accounts)."""

from __future__ import annotations

import os

from .base import Backend, BackendError


class AnthropicBackend(Backend):
    name = "anthropic"

    def __init__(self, model: str, api_key: str | None = None):
        super().__init__(model)
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise BackendError("install `anthropic` to use this backend") from e
        self._client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def chat(self, system: str, user: str, max_tokens: int = 800) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
