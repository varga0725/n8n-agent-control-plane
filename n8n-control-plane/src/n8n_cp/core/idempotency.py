"""Idempotency helpers, used mainly before execution *retry*.

The n8n API does not take an idempotency key, so safety here is about deciding
whether re-running an execution is safe at all. Re-running a workflow that sent a
payment or an email is not idempotent and must never be auto-retried. We infer
risk from the node types involved in the failed execution.
"""
from __future__ import annotations

from typing import Any

# Node-type / operation substrings that indicate a NON-idempotent side effect.
NON_IDEMPOTENT_HINTS = (
    "stripe", "paypal", "payment", "invoice", "billing", "charge",
    "sendemail", "emailsend", "gmail", "mailgun", "sendgrid", "smtp",
    "slack", "telegram", "discord", "twilio", "sms", "whatsapp",
    "order", "checkout", "booking", "reservation",
    "insert", "create", "post", "delete", "update", "upsert",
    "salesforce", "hubspot", "crm",
)
# Hints that a node is a safe read.
READ_HINTS = ("get", "read", "list", "search", "fetch", "lookup")


def execution_is_retry_safe(execution: dict) -> tuple[bool, list[str]]:
    """Heuristic: inspect the executed nodes for side-effecting operations.

    Returns (safe, reasons). Conservative: if anything looks non-idempotent we
    return False. Absence of evidence is treated as unsafe for write-capable
    workflows, so the caller routes to manual review rather than auto-retry.
    """
    reasons: list[str] = []
    node_types = _collect_node_types(execution)
    if not node_types:
        return False, ["Could not determine executed nodes — manual review required."]

    risky = []
    for t in node_types:
        low = t.lower()
        if any(h in low for h in NON_IDEMPOTENT_HINTS) and not any(
                r in low for r in READ_HINTS):
            risky.append(t)
    if risky:
        reasons.append("Non-idempotent side-effecting nodes detected: "
                       + ", ".join(sorted(set(risky))))
        return False, reasons
    reasons.append("No obviously side-effecting nodes detected; verify before retry.")
    return True, reasons


def _collect_node_types(execution: dict) -> list[str]:
    data = execution.get("data", execution)
    types: list[str] = []
    # Try workflowData.nodes first (present in detailed execution responses).
    wf = (data.get("workflowData") or {}) if isinstance(data, dict) else {}
    for n in wf.get("nodes", []) or []:
        if n.get("type"):
            types.append(n["type"])
    return types
