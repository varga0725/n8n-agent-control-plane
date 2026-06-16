"""Recursive secret redaction.

Applied to everything that could leave the process: tool output, audit records,
error details, and (when N8N_REDACT_EXECUTION_DATA is on) execution payloads.
The match is case-insensitive and substring-based on the *key*, so ``apiKey``,
``X-Api-Key`` and ``my_api_key_v2`` all redact.
"""
from __future__ import annotations

from typing import Any

REDACTED = "[REDACTED]"

# Keys whose *values* must never be emitted. Substring, case-insensitive.
SECRET_KEY_HINTS = (
    "password",
    "passphrase",
    "apikey",
    "api_key",
    "token",
    "accesstoken",
    "access_token",
    "refreshtoken",
    "refresh_token",
    "secret",
    "clientsecret",
    "client_secret",
    "privatekey",
    "private_key",
    "authorization",
    "cookie",
    "session",
    "webhooksecret",
    "webhook_secret",
    "credentials",  # n8n credential `data` blobs
    "x-n8n-api-key",
)


# Keys that look secret-ish but are deliberately safe to surface. The
# confirmation token is a short-lived, operation-bound approval handle that the
# agent MUST show the user — it is not a credential.
ALLOWLIST = (
    "confirmationtoken",  # our own approval handle
)


def _is_secret_key(key: str) -> bool:
    k = key.lower().replace("-", "").replace("_", "")
    if any(allow in k for allow in ALLOWLIST):
        return False
    return any(hint.replace("-", "").replace("_", "") in k for hint in SECRET_KEY_HINTS)


def redact(value: Any, _depth: int = 0) -> Any:
    """Return a deep copy of ``value`` with secret-looking fields masked.

    Lists, tuples and nested dicts are all traversed. A depth guard prevents
    pathological recursion on cyclic-ish structures.
    """
    if _depth > 64:
        return value
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            if isinstance(k, str) and _is_secret_key(k):
                out[k] = REDACTED
            else:
                out[k] = redact(v, _depth + 1)
        return out
    if isinstance(value, (list, tuple)):
        return [redact(v, _depth + 1) for v in value]
    return value


def redact_text(text: str, secrets: list[str]) -> str:
    """Mask any literal secret strings that appear in free text (e.g. the API
    key accidentally embedded in a URL or message)."""
    out = text
    for s in secrets:
        if s:
            out = out.replace(s, REDACTED)
    return out
