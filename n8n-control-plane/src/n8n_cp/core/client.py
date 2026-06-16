"""The safe n8n client — where transport, retry, errors, risk gating, audit and
redaction come together.

Two layers:
  * ``call`` / ``get`` / ``post`` ... — low-level: perform a request, retry
    transient failures, raise a normalized :class:`N8nError` on API errors.
  * ``execute`` — high-level: wrap a single operation with risk gating,
    confirmation enforcement, audit logging and the standard response envelope.
    Both the primitive tools and the high-level operations go through this.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Optional

from .config import Config, load_config
from .audit import AuditLogger
from .errors import (N8nError, classify_http, new_audit_id,
                     success_envelope, error_envelope)
from .risk import RiskLevel, gate_reason
from .confirmation import issue_token, verify_token
from . import retry as retry_mod
from . import pagination
from ..transports.base import Transport, RawResponse
from ..transports.rest import RestApiTransport


class N8nClient:
    def __init__(self, config: Optional[Config] = None,
                 transport: Optional[Transport] = None,
                 audit: Optional[AuditLogger] = None,
                 actor: str = "agent"):
        self.config = config or load_config()
        self.transport = transport or RestApiTransport(self.config.api_root,
                                                       self.config.api_key)
        self.audit = audit or AuditLogger(self.config.audit_dir,
                                          self.config.audit_log_enabled, actor)
        self.actor = actor

    # ----- low level -------------------------------------------------------
    def _raw(self, method: str, path: str, query: Optional[dict],
             body: Optional[Any]) -> RawResponse:
        """Perform a request, retrying only transient failures."""
        attempt = 0
        max_attempts = max(1, self.config.max_retries + 1)
        while True:
            attempt += 1
            try:
                resp = self.transport.request(
                    method, path, query=query, body=body,
                    timeout_ms=self.config.request_timeout_ms)
            except Exception as exc:  # network-level
                if retry_mod.is_retryable_network(exc) and attempt < max_attempts:
                    retry_mod.sleep_ms(retry_mod.backoff_delay_ms(attempt))
                    continue
                raise N8nError("network_error", f"Request failed: {type(exc).__name__}",
                               retryable=True)
            if resp.status in retry_mod.RETRYABLE_STATUS and attempt < max_attempts:
                ra = _retry_after_seconds(resp.headers)
                retry_mod.sleep_ms(retry_mod.backoff_delay_ms(attempt, ra))
                continue
            return resp

    def call(self, method: str, path: str, *, query: Optional[dict] = None,
             body: Optional[Any] = None) -> Any:
        """Return the parsed body, or raise N8nError on a non-2xx response."""
        resp = self._raw(method, path, query, body)
        if not resp.ok:
            raise classify_http(resp.status, resp.body)
        return resp.body

    def get(self, path, **kw):
        return self.call("GET", path, **kw)

    def post(self, path, **kw):
        return self.call("POST", path, **kw)

    def put(self, path, **kw):
        return self.call("PUT", path, **kw)

    def patch(self, path, **kw):
        return self.call("PATCH", path, **kw)

    def delete(self, path, **kw):
        return self.call("DELETE", path, **kw)

    def paginate(self, path: str, *, query: Optional[dict] = None,
                 max_items: int = pagination.MAX_ITEMS_PER_OPERATION):
        """Collect items across cursor pages with the global volume guard."""
        base_q = dict(query or {})
        base_q.setdefault("limit", pagination.DEFAULT_LIMIT)

        def fetch(cursor):
            q = dict(base_q)
            if cursor:
                q["cursor"] = cursor
            return self.call("GET", path, query=q)

        return pagination.collect(fetch, max_items=max_items)

    # ----- high level (safe execution) -------------------------------------
    def execute(self, *, operation: str, method: str, path: str,
                risk: RiskLevel, resource_type: str,
                resource_id: Optional[str] = None,
                query: Optional[dict] = None, body: Optional[Any] = None,
                dry_run: bool = False, confirm_token: Optional[str] = None,
                warnings: Optional[list] = None,
                impact: Optional[dict] = None) -> dict:
        """Run one operation safely and return the standard envelope.

        Gating order: risk policy -> confirmation -> (dry-run? stop) -> call.
        On a blocked confirmation step we mint a fresh, operation-bound token and
        return it with the impact summary so the agent can show the human and
        re-call with it.
        """
        started = time.time()
        audit_id = new_audit_id()
        warnings = list(warnings or [])

        confirmed = False
        if risk.requires_confirmation and confirm_token:
            ok, reason = verify_token(confirm_token, operation, resource_id)
            if not ok:
                err = N8nError("confirmation_error", reason, retryable=False)
                return self._finish_error(operation, risk, resource_type,
                                          resource_id, err, audit_id, started,
                                          dry_run, confirmed=False,
                                          req={"query": query, "body": body})
            confirmed = True

        block = gate_reason(risk, self.config.allow_destructive,
                            self.config.allow_production_writes, confirmed)
        if block is not None:
            # Provide an actionable next step: the impact summary + a token.
            token = issue_token(operation, resource_id)
            err = N8nError(
                "confirmation_required" if "confirmation" in block else "policy_blocked",
                block, status_code=None, retryable=False,
                details={"impact": impact or {},
                         "confirmationToken": token,
                         "howTo": "Re-call this tool with confirm_token set to the "
                                  "token above after a human approves the impact."})
            return self._finish_error(operation, risk, resource_type, resource_id,
                                      err, audit_id, started, dry_run, confirmed,
                                      req={"query": query, "body": body})

        if dry_run:
            data = {"dryRun": True, "wouldCall": f"{method} {path}",
                    "impact": impact or {}, "body": body, "query": query}
            env = success_envelope(operation, risk, resource_type, resource_id,
                                   data, warnings=warnings + ["Dry run: no request sent."],
                                   audit_id=audit_id, started=started, dry_run=True)
            self._audit(audit_id, operation, resource_type, resource_id, risk,
                        confirmed, True, {"query": query, "body": body},
                        {"dryRun": True}, True, env["durationMs"])
            return env

        try:
            data = self.call(method, path, query=query, body=body)
        except N8nError as err:
            return self._finish_error(operation, risk, resource_type, resource_id,
                                      err, audit_id, started, dry_run, confirmed,
                                      req={"query": query, "body": body})

        next_cursor = data.get("nextCursor") if isinstance(data, dict) else None
        env = success_envelope(operation, risk, resource_type, resource_id, data,
                               warnings=warnings, next_cursor=next_cursor,
                               audit_id=audit_id, started=started)
        self._audit(audit_id, operation, resource_type, resource_id, risk,
                    confirmed, False, {"query": query, "body": body},
                    {"ok": True}, True, env["durationMs"])
        return env

    # ----- helpers ---------------------------------------------------------
    def _finish_error(self, operation, risk, resource_type, resource_id, err,
                      audit_id, started, dry_run, confirmed, req) -> dict:
        env = error_envelope(operation, risk, err, audit_id=audit_id,
                             started=started, dry_run=dry_run)
        self._audit(audit_id, operation, resource_type, resource_id, risk,
                    confirmed, dry_run, req, {"error": err.type}, False,
                    env["durationMs"])
        return env

    def _audit(self, audit_id, operation, resource_type, resource_id, risk,
               confirmed, dry_run, req, resp, success, duration_ms):
        self.audit.record(audit_id=audit_id, operation=operation,
                          resource_type=resource_type, resource_id=resource_id,
                          risk=risk, confirmed=confirmed, dry_run=dry_run,
                          request_summary=req, response_summary=resp,
                          success=success, duration_ms=duration_ms)


def _retry_after_seconds(headers: dict) -> Optional[float]:
    for k, v in (headers or {}).items():
        if k.lower() == "retry-after":
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
    return None
