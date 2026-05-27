"""Ollama backend (local, free).

Runs against an Ollama server (default ``http://localhost:11434``). Good for
NYU Torch sessions: pull a 70B-class open-weights model once, then every
eval run is free.

    ollama pull llama3.1:70b
    ollama serve
    a11yeval --target ollama:llama3.1:70b
"""

from __future__ import annotations

import os

import httpx

from .base import Backend, BackendError


class OllamaBackend(Backend):
    name = "ollama"

    def __init__(self, model: str, base_url: str | None = None, timeout: float = 300.0):
        super().__init__(model)
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout = timeout

    def chat(self, system: str, user: str, max_tokens: int = 800) -> str:
        try:
            r = httpx.post(
                f"{self.base_url.rstrip('/')}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except (httpx.HTTPError, KeyError) as e:
            raise BackendError(f"ollama call failed: {e}") from e
