"""Gemini backend (free tier on Google AI Studio).

Set ``GOOGLE_API_KEY`` (from https://aistudio.google.com). The free tier on
``gemini-2.0-flash`` is generous enough to run the full a11y eval many
times over.
"""

from __future__ import annotations

import os

import httpx

from .base import Backend, BackendError


class GeminiBackend(Backend):
    name = "gemini"

    def __init__(self, model: str, api_key: str | None = None, timeout: float = 120.0):
        super().__init__(model)
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise BackendError("set GOOGLE_API_KEY (or GEMINI_API_KEY) for the Gemini backend")
        self.timeout = timeout

    def chat(self, system: str, user: str, max_tokens: int = 800) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        try:
            r = httpx.post(
                url,
                params={"key": self.api_key},
                json={
                    "system_instruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (httpx.HTTPError, KeyError, IndexError) as e:
            raise BackendError(f"gemini call failed: {e}") from e
