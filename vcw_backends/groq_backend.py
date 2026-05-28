"""Groq backend (free tier).

Set ``GROQ_API_KEY`` (from https://console.groq.com). Groq serves open-weights
models (Llama 3.x, Mixtral) at very high throughput on the free tier.
OpenAI-compatible API.
"""

from __future__ import annotations

import os

import httpx

from ._retry import post_with_retry
from .base import Backend, BackendError


class GroqBackend(Backend):
    name = "groq"

    def __init__(self, model: str, api_key: str | None = None, timeout: float = 120.0):
        super().__init__(model)
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise BackendError("set GROQ_API_KEY for the Groq backend")
        self.timeout = timeout

    def chat(self, system: str, user: str, max_tokens: int = 800) -> str:
        try:
            r = post_with_retry(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": max_tokens,
                },
                timeout=self.timeout,
            )
            return r.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError) as e:
            raise BackendError(f"groq call failed: {e}") from e
