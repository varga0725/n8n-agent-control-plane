"""Shared helpers for instance-wide operations."""
from __future__ import annotations

from ..tools import run_tool
from ._util import unwrap


def safe_list(client, tool, query=None):
    env = run_tool(tool, query or {}, client=client)
    if not env.get("success"):
        return None, env.get("error")
    data = unwrap(env)
    if isinstance(data, dict) and "data" in data:
        return data["data"], None
    return data, None


def audit_summary(audit) -> dict:
    if not isinstance(audit, dict):
        return {"raw": str(audit)[:500]}
    out = {}
    for section, content in audit.items():
        if isinstance(content, dict):
            risk = content.get("risk") or content.get("riskLevel")
            sections = content.get("sections") or []
            out[section] = {"risk": risk, "issueCount": len(sections) if sections else None}
    return out or {"keys": list(audit.keys())}


def looks_secret(value: str) -> bool:
    if len(value) < 16:
        return False
    return any(c.isalpha() for c in value) and any(c.isdigit() for c in value)
