"""Capability discovery.

Before acting, ask the instance what it supports via ``GET /discover`` (n8n
1.1.x). From the result we build a registry the tool layer consults: a tool is
only allowed to run if its domain is available, it is not a disabled beta, and
nothing in the discover payload marks it unsupported.

``/discover`` shapes vary across n8n versions, so parsing is defensive: we look
for common keys and fall back to "assume the documented baseline is available"
rather than hard-failing. Anything explicitly flagged disabled is respected.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Domains that exist on every supported n8n with the Public API enabled.
BASELINE_DOMAINS = {
    "workflows", "executions", "credentials", "tags",
}
# Domains that depend on edition / feature flags.
OPTIONAL_DOMAINS = {
    "users", "projects", "folders", "variables", "data-tables",
    "insights", "source-control", "community-packages", "n8n-packages",
    "audit", "discover",
}


@dataclass
class Capabilities:
    raw: dict = field(default_factory=dict)
    available_domains: set[str] = field(default_factory=set)
    disabled: set[str] = field(default_factory=set)
    discover_supported: bool = False

    def is_available(self, domain: str) -> bool:
        if domain in self.disabled:
            return False
        if domain in BASELINE_DOMAINS:
            return True
        return domain in self.available_domains

    def reason_unavailable(self, domain: str) -> Optional[str]:
        if domain in self.disabled:
            return f"Domain '{domain}' is disabled on this instance."
        if self.is_available(domain):
            return None
        if not self.discover_supported:
            return (f"Domain '{domain}' could not be confirmed: this instance does "
                    f"not expose /discover, so optional/beta features are treated as "
                    f"unavailable. Enable it or pass --force if you are sure.")
        return f"Domain '{domain}' is not available on this instance per /discover."


def fetch_capabilities(client) -> Capabilities:
    """Call /discover and build a Capabilities object. Never raises — a missing
    /discover yields a conservative baseline."""
    caps = Capabilities()
    try:
        raw = client.get("/discover")
    except Exception:
        # No /discover -> baseline only, optional features unconfirmed.
        caps.available_domains = set(BASELINE_DOMAINS)
        return caps

    caps.raw = raw if isinstance(raw, dict) else {"data": raw}
    caps.discover_supported = True
    caps.available_domains = set(BASELINE_DOMAINS) | _extract_domains(caps.raw)
    caps.disabled = _extract_disabled(caps.raw)
    return caps


def _extract_domains(raw: dict) -> set[str]:
    found: set[str] = set()
    blob = raw.get("data", raw)
    # Common shapes: {"features": {...}}, {"capabilities": [...]}, {"endpoints":[...]}
    for key in ("features", "capabilities", "modules", "endpoints", "domains"):
        v = blob.get(key) if isinstance(blob, dict) else None
        if isinstance(v, dict):
            found |= {k for k, on in v.items() if on}
        elif isinstance(v, list):
            found |= {str(x).strip("/").split("/")[0] for x in v if x}
    # Feature-flag style booleans, e.g. {"dataTables": true}
    if isinstance(blob, dict):
        for k, val in blob.items():
            if val is True:
                found.add(_normalize(k))
    return {_normalize(d) for d in found}


def _extract_disabled(raw: dict) -> set[str]:
    blob = raw.get("data", raw)
    disabled: set[str] = set()
    if isinstance(blob, dict):
        for k, val in blob.items():
            if val is False:
                disabled.add(_normalize(k))
    return disabled


def _normalize(name: str) -> str:
    n = str(name).lower()
    aliases = {
        "datatables": "data-tables", "data_tables": "data-tables",
        "sourcecontrol": "source-control", "source_control": "source-control",
        "communitypackages": "community-packages",
        "n8npackages": "n8n-packages",
    }
    return aliases.get(n.replace("-", "").replace("_", ""), n)
