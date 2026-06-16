"""Retry with exponential backoff + jitter.

Only transient, idempotent-safe failures are retried. The decision is made from
the HTTP status / error type, never blindly. ``Retry-After`` is honored.
"""
from __future__ import annotations

import random
import time
from typing import Optional

# Statuses we may retry (transient). Everything else is surfaced immediately.
RETRYABLE_STATUS = {429, 502, 503, 504}
# Network-level exception markers (by class name) we treat as transient.
RETRYABLE_NETWORK = ("timeout", "connectionreset", "connectionerror",
                     "urlerror", "remotedisconnected")

# Base schedule (ms) per the spec: 500, 1500, 3500 ...
_BASE_DELAYS_MS = (500, 1500, 3500)


def is_retryable_status(status: int) -> bool:
    return status in RETRYABLE_STATUS


def is_retryable_network(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    return any(marker in name for marker in RETRYABLE_NETWORK)


def backoff_delay_ms(attempt: int, retry_after_s: Optional[float] = None) -> float:
    """Delay before the given attempt (1-based). Honors Retry-After if present."""
    if retry_after_s is not None and retry_after_s >= 0:
        return retry_after_s * 1000.0
    base = _BASE_DELAYS_MS[min(attempt - 1, len(_BASE_DELAYS_MS) - 1)]
    jitter = random.uniform(0, base * 0.25)
    return base + jitter


def sleep_ms(ms: float) -> None:
    time.sleep(ms / 1000.0)
