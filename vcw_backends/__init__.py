"""Pluggable chat backends for the VCW harness.

A backend is anything that implements ``chat(system, user, max_tokens) -> str``.
Selection is by spec string: ``<provider>:<model>``.

Examples:
    anthropic:claude-sonnet-4-6
    ollama:llama3.1:70b          (note: model contains a colon — handled)
    gemini:gemini-2.0-flash
    groq:llama-3.1-70b-versatile
"""

from .base import Backend, BackendError
from .factory import make_backend, parse_spec

__all__ = ["Backend", "BackendError", "make_backend", "parse_spec"]
