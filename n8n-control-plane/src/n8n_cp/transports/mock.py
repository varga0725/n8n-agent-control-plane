"""In-memory mock transport for offline tests and dry demos.

You can preload canned responses keyed by "METHOD /path" (path may contain the
exact substituted ids), or register a handler callable for dynamic behavior.
Unmatched requests return a 404 so tests fail loudly rather than silently.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from .base import RawResponse


class MockTransport:
    def __init__(self):
        self._canned: dict[str, RawResponse] = {}
        self._handlers: list[Callable[[str, str, dict, Any], Optional[RawResponse]]] = []
        self.calls: list[dict] = []  # recorded for assertions

    def stub(self, method: str, path: str, status: int, body: Any,
             headers: Optional[dict] = None) -> "MockTransport":
        self._canned[f"{method.upper()} {path}"] = RawResponse(status, body, headers or {})
        return self

    def handler(self, fn: Callable[[str, str, dict, Any], Optional[RawResponse]]) -> "MockTransport":
        self._handlers.append(fn)
        return self

    def request(self, method: str, path: str, *,
                query: Optional[dict] = None,
                body: Optional[Any] = None,
                timeout_ms: int = 30000) -> RawResponse:
        self.calls.append({"method": method.upper(), "path": path,
                           "query": query or {}, "body": body})
        key = f"{method.upper()} {path}"
        if key in self._canned:
            return self._canned[key]
        for fn in self._handlers:
            r = fn(method.upper(), path, query or {}, body)
            if r is not None:
                return r
        return RawResponse(404, {"message": f"No mock for {key}"})
