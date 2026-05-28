"""Factory for backend spec strings.

A spec is ``<provider>:<model>``. Provider names: ``anthropic``, ``ollama``,
``gemini``, ``groq``. The model component may itself contain colons (e.g.
``ollama:llama3.1:70b``) — only the first colon is the separator.

Bare names without a colon are treated as Anthropic models for backward
compatibility with the original CLI.
"""

from __future__ import annotations

from .base import Backend, BackendError

_PROVIDERS = {"anthropic", "ollama", "gemini", "groq", "lmstudio"}


def parse_spec(spec: str) -> tuple[str, str]:
    """Return ``(provider, model)``."""
    if ":" not in spec:
        return "anthropic", spec
    head, _, tail = spec.partition(":")
    if head not in _PROVIDERS:
        return "anthropic", spec
    return head, tail


def make_backend(spec: str, **kwargs) -> Backend:
    provider, model = parse_spec(spec)
    if provider == "anthropic":
        from .anthropic_backend import AnthropicBackend

        return AnthropicBackend(model=model, **kwargs)
    if provider == "ollama":
        from .ollama_backend import OllamaBackend

        return OllamaBackend(model=model, **kwargs)
    if provider == "gemini":
        from .gemini_backend import GeminiBackend

        return GeminiBackend(model=model, **kwargs)
    if provider == "groq":
        from .groq_backend import GroqBackend

        return GroqBackend(model=model, **kwargs)
    if provider == "lmstudio":
        from .lmstudio_backend import LMStudioBackend

        return LMStudioBackend(model=model, **kwargs)
    raise BackendError(f"unknown provider: {provider}")
