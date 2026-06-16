"""Domain: insights. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_insights_summary",
]

def summary(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /insights/summary — risk: read_only. Performance / execution insights summary."""
    return run_tool("n8n_insights_summary", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
