"""Domain: users. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_user_list",
    "n8n_user_get",
    "n8n_user_create",
    "n8n_user_update_role",
    "n8n_user_delete",
]

def list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /users — risk: read_only. List users."""
    return run_tool("n8n_user_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /users/{id} — risk: read_only. Get a user by id or email."""
    return run_tool("n8n_user_get", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def create(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /users — risk: production_impact. Create user(s) (access change; dedup emails)."""
    return run_tool("n8n_user_create", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update_role(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PATCH /users/{id}/role — risk: production_impact. Change a user's global role (owner changes are high risk)."""
    return run_tool("n8n_user_update_role", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /users/{id} — risk: destructive. Delete a user (destructive; owner deletion guarded)."""
    return run_tool("n8n_user_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
