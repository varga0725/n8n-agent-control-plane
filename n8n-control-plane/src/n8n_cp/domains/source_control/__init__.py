"""Domain: source-control. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_source_control_pull",
]

def pull(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /source-control/pull — risk: production_impact. Pull from the connected git remote (production-impact)."""
    return run_tool("n8n_source_control_pull", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
