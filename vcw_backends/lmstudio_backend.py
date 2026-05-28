"""LM Studio backend (local, free, no API key).

Talks to LM Studio's OpenAI-compatible server (default
``http://localhost:1234/v1``). Start it with ``lms server start`` and load
a model with ``lms load <model>``, then:

    a11yeval --target "lmstudio:llama-3.2-3b-instruct"

The model name is whatever LM Studio reports for the loaded model; if you
leave it blank LM Studio routes to the currently-loaded model.
"""

from __future__ import annotations

import os

import httpx

from ._retry import post_with_retry
from .base import Backend, BackendError


class LMStudioBackend(Backend):
    name = "lmstudio"

    def __init__(self, model: str = "", base_url: str | None = None, timeout: float = 600.0):
        super().__init__(model)
        self.base_url = base_url or os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        self.timeout = timeout

    def chat(self, system: str, user: str, max_tokens: int = 800) -> str:
        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
        }
        if self.model:
            payload["model"] = self.model
        try:
            r = post_with_retry(
                f"{self.base_url.rstrip('/')}/chat/completions",
                json=payload,
                timeout=self.timeout,
            )
            return r.json()["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError) as e:
            raise BackendError(f"lmstudio call failed: {e}") from e
