"""Authentication.

n8n's Public API authenticates with the ``X-N8N-API-KEY`` header. This module
centralizes how that header is built so no other code handles the raw key. The
key is read from configuration only and is never logged or serialized.
"""
from __future__ import annotations

from typing import Optional

API_KEY_HEADER = "X-N8N-API-KEY"


def auth_headers(api_key: Optional[str]) -> dict:
    """Return the auth headers for a request, or an empty dict if no key is set
    (dry-run / doctor still work without a key)."""
    return {API_KEY_HEADER: api_key} if api_key else {}


def redact_url(url: str, api_key: Optional[str]) -> str:
    """Defensive: ensure a key never survives in a URL we might surface."""
    if api_key:
        return url.replace(api_key, "[REDACTED]")
    return url
