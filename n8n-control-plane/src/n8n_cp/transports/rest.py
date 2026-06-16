"""REST transport over the n8n Public API using only the Python stdlib.

No third-party dependency so the package runs anywhere a Python interpreter
exists. The API key is attached here as the ``X-N8N-API-KEY`` header and never
logged.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from .base import RawResponse
from ..core.auth import auth_headers


class RestApiTransport:
    def __init__(self, api_root: str, api_key: str):
        self._api_root = api_root.rstrip("/")
        self._api_key = api_key

    def request(self, method: str, path: str, *,
                query: Optional[dict] = None,
                body: Optional[Any] = None,
                timeout_ms: int = 30000) -> RawResponse:
        url = self._api_root + path
        if query:
            clean = {k: v for k, v in query.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean, doseq=True)

        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method.upper())
        req.add_header("Accept", "application/json")
        for hk, hv in auth_headers(self._api_key).items():
            req.add_header(hk, hv)
        if data is not None:
            req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=timeout_ms / 1000.0) as resp:
                raw = resp.read().decode() or ""
                parsed = json.loads(raw) if raw.strip().startswith(("{", "[")) else raw
                return RawResponse(resp.status, parsed, dict(resp.headers))
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace") if e.fp else ""
            try:
                parsed = json.loads(raw) if raw.strip().startswith(("{", "[")) else {"raw": raw}
            except json.JSONDecodeError:
                parsed = {"raw": raw[:1000]}
            return RawResponse(e.code, parsed, dict(e.headers or {}))
        # URLError (network) is allowed to propagate; the client classifies it
        # as a transient network failure and applies the retry policy.
