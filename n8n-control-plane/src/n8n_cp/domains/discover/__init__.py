"""Domain: discover. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_discover_capabilities",
]

def capabilities(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /discover — risk: read_only. Discover which API features this instance supports."""
    return run_tool("n8n_discover_capabilities", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
