"""Shared helpers for operations: a step-tracing result builder."""
from __future__ import annotations

import time
from typing import Any, Optional

from ..core.errors import new_audit_id
from ..core.redaction import redact


class OpResult:
    """Accumulates an ordered, redacted trace of steps for one operation."""

    def __init__(self, operation: str):
        self.operation = operation
        self.audit_id = new_audit_id()
        self.started = time.time()
        self.steps: list[dict] = []
        self.warnings: list[str] = []
        self.success = True
        self.data: dict = {}
        self.error: Optional[dict] = None

    def step(self, name: str, status: str = "ok", **detail) -> "OpResult":
        self.steps.append({"step": name, "status": status, **redact(detail)})
        return self

    def warn(self, msg: str) -> "OpResult":
        self.warnings.append(msg)
        return self

    def fail(self, type_: str, message: str, **detail) -> "OpResult":
        self.success = False
        self.error = {"type": type_, "message": message, "details": redact(detail)}
        self.step("failed", status="error", type=type_, message=message)
        return self

    def finish(self, **data) -> dict:
        self.data.update(data)
        return {
            "success": self.success,
            "operation": self.operation,
            "auditId": self.audit_id,
            "durationMs": int((time.time() - self.started) * 1000),
            "steps": self.steps,
            "warnings": self.warnings,
            "data": redact(self.data),
            "error": self.error,
        }


def unwrap(envelope_or_data: Any) -> Any:
    """Get the payload out of a tool envelope or a raw API response."""
    if isinstance(envelope_or_data, dict):
        if "data" in envelope_or_data and "success" in envelope_or_data:
            return envelope_or_data["data"]
        if "data" in envelope_or_data:
            return envelope_or_data["data"]
    return envelope_or_data
