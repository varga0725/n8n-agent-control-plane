"""Domain: n8n-packages. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_package_export",
    "n8n_package_import",
]

def package_export(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /n8n-packages/export — risk: reversible_write. Export workflows to n8n package format (beta)."""
    return run_tool("n8n_package_export", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def package_import(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /n8n-packages/import — risk: production_impact. Import an n8n package (beta)."""
    return run_tool("n8n_package_import", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
