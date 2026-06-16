"""Structured audit logging.

Every write (and optionally every read) appends one JSON line to a daily audit
file. Records are redacted before they are written — no API key, no secrets, no
raw personal execution data.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

from .redaction import redact
from .risk import RiskLevel


def _summary(obj: Any, limit: int = 2000) -> Any:
    """A compact, redacted summary safe to persist."""
    red = redact(obj)
    text = json.dumps(red, default=str)
    if len(text) <= limit:
        return red
    return {"_truncated": True, "preview": text[:limit]}


class AuditLogger:
    def __init__(self, audit_dir: str, enabled: bool = True, actor: str = "agent"):
        self.audit_dir = audit_dir
        self.enabled = enabled
        self.actor = actor

    def record(self, *, audit_id: str, operation: str, resource_type: str,
               resource_id: Optional[str], risk: RiskLevel, confirmed: bool,
               dry_run: bool, request_summary: Any, response_summary: Any,
               success: bool, duration_ms: int) -> dict:
        entry = {
            "auditId": audit_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.actor,
            "operation": operation,
            "resourceType": resource_type,
            "resourceId": resource_id,
            "riskLevel": risk.value,
            "confirmed": confirmed,
            "dryRun": dry_run,
            "requestSummary": _summary(request_summary),
            "responseSummary": _summary(response_summary),
            "success": success,
            "durationMs": duration_ms,
        }
        if self.enabled:
            self._append(entry)
        return entry

    def _append(self, entry: dict) -> None:
        try:
            os.makedirs(self.audit_dir, exist_ok=True)
            day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            path = os.path.join(self.audit_dir, f"audit-{day}.jsonl")
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except OSError:
            # Auditing must never crash the operation; degrade quietly but the
            # entry is still returned to the caller for in-memory inspection.
            pass
