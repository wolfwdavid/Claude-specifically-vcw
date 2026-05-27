"""Spec parsing and factory dispatch — no network calls."""

from __future__ import annotations

import pytest

from vcw_backends import make_backend, parse_spec
from vcw_backends.base import BackendError


def test_parse_bare_name_is_anthropic():
    assert parse_spec("claude-sonnet-4-6") == ("anthropic", "claude-sonnet-4-6")


def test_parse_explicit_anthropic():
    assert parse_spec("anthropic:claude-opus-4-7") == ("anthropic", "claude-opus-4-7")


def test_parse_ollama_with_colon_in_model():
    assert parse_spec("ollama:llama3.1:70b") == ("ollama", "llama3.1:70b")


def test_parse_gemini():
    assert parse_spec("gemini:gemini-2.0-flash") == ("gemini", "gemini-2.0-flash")


def test_parse_groq():
    assert parse_spec("groq:llama-3.1-70b-versatile") == ("groq", "llama-3.1-70b-versatile")


def test_unknown_prefix_falls_back_to_anthropic():
    # Defensive: if someone passes "foo:bar" we treat it as the Anthropic model "foo:bar"
    # rather than crashing. Anthropic call will fail later if the model name is invalid.
    assert parse_spec("foo:bar") == ("anthropic", "foo:bar")


def test_factory_rejects_unknown_provider_via_make_backend(monkeypatch):
    # Force parse_spec to claim an unknown provider so we exercise the factory's guard.
    import vcw_backends.factory as f

    monkeypatch.setattr(f, "parse_spec", lambda spec: ("nope", spec))
    with pytest.raises(BackendError):
        make_backend("nope:model")


def test_make_ollama_does_not_require_api_key(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    b = make_backend("ollama:llama3.1:70b")
    assert b.model == "llama3.1:70b"
    assert b.base_url.startswith("http")


def test_make_gemini_errors_without_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(BackendError):
        make_backend("gemini:gemini-2.0-flash")


def test_make_groq_errors_without_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(BackendError):
        make_backend("groq:llama-3.1-70b-versatile")
