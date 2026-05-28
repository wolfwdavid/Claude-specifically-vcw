"""Retry-with-backoff wrapper for HTTP backends.

Free-tier providers (Groq, Gemini) routinely return 429 under modest load.
A bounded retry with exponential backoff turns rate-limit responses into
slowdowns rather than hard failures, which is what the harness actually
wants — running an eval over many cases is exactly the workload providers
rate-limit, and the right answer is to wait, not to abandon the run.

Honors the ``Retry-After`` header when present.
"""

from __future__ import annotations

import time
from typing import Callable

import httpx


_RETRY_STATUS = {408, 429, 500, 502, 503, 504}


def post_with_retry(
    url: str,
    *,
    max_attempts: int = 8,
    initial_backoff: float = 2.0,
    backoff_factor: float = 2.0,
    max_backoff: float = 60.0,
    on_retry: Callable[[int, float, int | None], None] | None = None,
    **kwargs,
) -> httpx.Response:
    """``httpx.post`` with retry on rate-limit and transient server errors."""
    backoff = initial_backoff
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            r = httpx.post(url, **kwargs)
            if r.status_code in _RETRY_STATUS:
                retry_after = _parse_retry_after(r.headers.get("Retry-After"))
                wait = retry_after if retry_after is not None else min(backoff, max_backoff)
                if on_retry:
                    on_retry(attempt, wait, r.status_code)
                if attempt == max_attempts:
                    r.raise_for_status()
                time.sleep(wait)
                backoff = min(backoff * backoff_factor, max_backoff)
                continue
            r.raise_for_status()
            return r
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
            last_err = e
            wait = min(backoff, max_backoff)
            if on_retry:
                on_retry(attempt, wait, None)
            if attempt == max_attempts:
                raise
            time.sleep(wait)
            backoff = min(backoff * backoff_factor, max_backoff)
    assert last_err is not None
    raise last_err  # pragma: no cover


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
