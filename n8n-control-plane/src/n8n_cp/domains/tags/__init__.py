"""Domain: tags. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_tag_create",
    "n8n_tag_list",
    "n8n_tag_get",
    "n8n_tag_update",
    "n8n_tag_delete",
]

def create(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /tags — risk: reversible_write. Create a tag (dedup by name)."""
    return run_tool("n8n_tag_create", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /tags — risk: read_only. List tags."""
    return run_tool("n8n_tag_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /tags/{id} — risk: read_only. Get a tag."""
    return run_tool("n8n_tag_get", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PUT /tags/{id} — risk: reversible_write. Rename a tag."""
    return run_tool("n8n_tag_update", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /tags/{id} — risk: destructive. Delete a tag (destructive)."""
    return run_tool("n8n_tag_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
