"""Operation-specific, short-lived confirmation tokens.

A confirmation token is bound to a *specific* operation + resource and expires
quickly. This prevents a generic "yes" from authorizing a later, different
destructive action. The agent flow is:

  1. Call the tool with dry_run/preview -> get an impact summary + a token.
  2. Show the impact summary to the human.
  3. Re-call the tool with the same token to actually execute.

Tokens are HMAC-signed over (operation, resource_id, expiry) using a per-process
secret, so they cannot be forged or reused across operations.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time

_PROCESS_SECRET = os.urandom(32)
_DEFAULT_TTL_S = 300  # 5 minutes


def _sign(payload: str) -> str:
    mac = hmac.new(_PROCESS_SECRET, payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(mac).decode().rstrip("=")[:24]


def issue_token(operation: str, resource_id: str | None, ttl_s: int = _DEFAULT_TTL_S) -> str:
    expiry = int(time.time()) + ttl_s
    rid = resource_id or "-"
    payload = f"{operation}|{rid}|{expiry}"
    sig = _sign(payload)
    raw = f"{expiry}.{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def verify_token(token: str, operation: str, resource_id: str | None) -> tuple[bool, str]:
    """Return (ok, reason). Reason is '' when ok."""
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode()).decode()
        expiry_str, sig = raw.split(".", 1)
        expiry = int(expiry_str)
    except Exception:
        return False, "Malformed confirmation token."
    if time.time() > expiry:
        return False, "Confirmation token has expired — re-run the preview to get a fresh one."
    rid = resource_id or "-"
    expected = _sign(f"{operation}|{rid}|{expiry}")
    if not hmac.compare_digest(sig, expected):
        return False, "Confirmation token does not match this operation/resource."
    return True, ""
