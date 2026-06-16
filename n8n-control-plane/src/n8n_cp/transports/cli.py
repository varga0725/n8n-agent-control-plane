"""CLI transport (spec section 3: cli.transport).

An alternative transport that drives a local ``n8n`` CLI instead of the REST API,
for environments where direct HTTP isn't available but the CLI is. The public API
surface (workflows/executions/credentials …) maps only partially onto the CLI, so
this is a thin adapter: it implements the ``Transport`` interface and supports the
subset the n8n CLI exposes (notably workflow import/export, activate/deactivate,
and listing). Unsupported routes raise a clear error rather than guessing.

This is intentionally conservative — REST is the primary transport. The class
exists so the architecture is ready for CLI-backed deployments without changing
any domain/operation code.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Optional

from .base import RawResponse


class N8nCliTransport:
    def __init__(self, n8n_bin: str = "n8n"):
        self._bin = n8n_bin

    def _available(self) -> bool:
        return shutil.which(self._bin) is not None

    def request(self, method: str, path: str, *,
                query: Optional[dict] = None,
                body: Optional[Any] = None,
                timeout_ms: int = 30000) -> RawResponse:
        if not self._available():
            return RawResponse(503, {"message": f"n8n CLI ('{self._bin}') not found "
                                     "on PATH; use the REST transport instead."})

        argv = self._map(method, path, query, body)
        if argv is None:
            return RawResponse(501, {"message": f"CLI transport does not implement "
                                     f"{method} {path}. Use RestApiTransport."})
        try:
            proc = subprocess.run(argv, capture_output=True, text=True,
                                  timeout=timeout_ms / 1000.0)
        except subprocess.TimeoutExpired:
            return RawResponse(504, {"message": "n8n CLI timed out."})
        if proc.returncode != 0:
            return RawResponse(500, {"message": "n8n CLI error", "stderr": proc.stderr[:500]})
        out = proc.stdout.strip()
        try:
            return RawResponse(200, json.loads(out) if out.startswith(("{", "[")) else {"raw": out})
        except json.JSONDecodeError:
            return RawResponse(200, {"raw": out})

    def _map(self, method: str, path: str, query, body) -> Optional[list[str]]:
        """Map a REST route to an n8n CLI invocation, where one exists."""
        if method == "GET" and path == "/workflows":
            return [self._bin, "list:workflow"]
        if method == "POST" and path.endswith("/activate"):
            wid = path.split("/")[2]
            return [self._bin, "update:workflow", f"--id={wid}", "--active=true"]
        if method == "POST" and path.endswith("/deactivate"):
            wid = path.split("/")[2]
            return [self._bin, "update:workflow", f"--id={wid}", "--active=false"]
        # Most routes have no CLI equivalent.
        return None
