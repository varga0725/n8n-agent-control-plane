"""Rate-limit handling (spec section 3: rate-limit).

n8n's Public API returns HTTP 429 with an optional ``Retry-After`` header when a
client is throttled. The retry layer (``core/retry.py``) treats 429 as a
transient, retryable status; this module owns the 429-specific concerns: reading
``Retry-After`` and providing a tiny client-side token-bucket throttle for
callers that want to self-limit bursts (e.g. bulk operations).
"""
from __future__ import annotations

import time
from typing import Optional


def parse_retry_after(headers: dict) -> Optional[float]:
    """Seconds to wait per a Retry-After header (numeric form), or None."""
    for k, v in (headers or {}).items():
        if k.lower() == "retry-after":
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
    return None


class TokenBucket:
    """Optional client-side throttle to avoid hammering the API in bulk loops."""

    def __init__(self, rate_per_sec: float = 10.0, burst: int = 10):
        self.rate = rate_per_sec
        self.capacity = burst
        self.tokens = float(burst)
        self.updated = time.monotonic()

    def acquire(self, n: int = 1) -> None:
        while True:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
            self.updated = now
            if self.tokens >= n:
                self.tokens -= n
                return
            time.sleep((n - self.tokens) / self.rate)
