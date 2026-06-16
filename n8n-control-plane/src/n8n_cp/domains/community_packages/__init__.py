"""Domain: community-packages. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_community_package_list",
    "n8n_community_package_install",
    "n8n_community_package_update",
    "n8n_community_package_uninstall",
]

def list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /community-packages — risk: read_only. List installed community packages."""
    return run_tool("n8n_community_package_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def install(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /community-packages — risk: production_impact. Install a community package."""
    return run_tool("n8n_community_package_install", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PATCH /community-packages/{name} — risk: production_impact. Update a community package."""
    return run_tool("n8n_community_package_update", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def uninstall(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /community-packages/{name} — risk: destructive. Uninstall a community package."""
    return run_tool("n8n_community_package_uninstall", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
