"""Domain: variables. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_variable_list",
    "n8n_variable_create",
    "n8n_variable_update",
    "n8n_variable_delete",
]

def list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /variables — risk: read_only. List variables."""
    return run_tool("n8n_variable_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def create(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /variables — risk: reversible_write. Create a variable (warns if value looks secret)."""
    return run_tool("n8n_variable_create", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PUT /variables/{id} — risk: reversible_write. Update a variable."""
    return run_tool("n8n_variable_update", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /variables/{id} — risk: destructive. Delete a variable (destructive)."""
    return run_tool("n8n_variable_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
