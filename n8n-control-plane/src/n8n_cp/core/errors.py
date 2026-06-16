"""Error normalization and the unified response envelope.

Callers (agents, CI) must never see a raw stack trace or an HTML error page.
Every n8n API error is mapped to a small, stable shape.
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from .risk import RiskLevel
from .redaction import redact


def new_audit_id() -> str:
    # Short, sortable-ish, unique enough for correlation.
    return "op_" + uuid.uuid4().hex[:20]


class N8nError(Exception):
    """Normalized error. Carries everything the envelope needs."""

    def __init__(self, type_: str, message: str, status_code: Optional[int] = None,
                 retryable: bool = False, details: Optional[dict] = None):
        super().__init__(message)
        self.type = type_
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "message": self.message,
            "statusCode": self.status_code,
            "retryable": self.retryable,
            "details": redact(self.details),
        }


# Map HTTP status -> (error type, retryable)
_STATUS_MAP = {
    400: ("validation_error", False),
    401: ("auth_error", False),
    403: ("permission_error", False),
    404: ("not_found", False),
    409: ("conflict", False),
    422: ("validation_error", False),
    429: ("rate_limited", True),
    500: ("server_error", False),
    502: ("upstream_error", True),
    503: ("service_unavailable", True),
    504: ("gateway_timeout", True),
}


def classify_http(status: int, body: Any) -> N8nError:
    type_, retryable = _STATUS_MAP.get(status, ("http_error", status >= 500))
    msg = _extract_message(body) or f"n8n API returned HTTP {status}."
    details = body if isinstance(body, dict) else {"raw": str(body)[:500]}
    return N8nError(type_, msg, status_code=status, retryable=retryable, details=details)


def _extract_message(body: Any) -> Optional[str]:
    if isinstance(body, dict):
        for key in ("message", "error", "detail", "hint"):
            v = body.get(key)
            if isinstance(v, str) and v:
                return v
    return None


def success_envelope(operation: str, risk: RiskLevel, resource_type: str,
                     resource_id: Optional[str], data: Any, *,
                     warnings: Optional[list] = None, next_cursor: Optional[str] = None,
                     audit_id: str, started: float, dry_run: bool = False) -> dict:
    return {
        "success": True,
        "operation": operation,
        "riskLevel": risk.value,
        "resourceType": resource_type,
        "resourceId": resource_id,
        "dryRun": dry_run,
        "data": redact(data),
        "warnings": warnings or [],
        "nextCursor": next_cursor,
        "auditId": audit_id,
        "durationMs": int((time.time() - started) * 1000),
    }


def error_envelope(operation: str, risk: RiskLevel, err: N8nError, *,
                   audit_id: str, started: float, dry_run: bool = False) -> dict:
    return {
        "success": False,
        "operation": operation,
        "riskLevel": risk.value,
        "dryRun": dry_run,
        "error": err.to_dict(),
        "auditId": audit_id,
        "durationMs": int((time.time() - started) * 1000),
    }
