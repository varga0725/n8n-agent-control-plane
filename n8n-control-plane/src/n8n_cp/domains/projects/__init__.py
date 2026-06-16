"""Domain: projects. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_project_list",
    "n8n_project_create",
    "n8n_project_update",
    "n8n_project_delete",
    "n8n_project_user_list",
    "n8n_project_user_add",
    "n8n_project_user_remove",
    "n8n_project_user_update_role",
]

def list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /projects — risk: read_only. List projects."""
    return run_tool("n8n_project_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def create(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /projects — risk: reversible_write. Create a project."""
    return run_tool("n8n_project_create", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PUT /projects/{projectId} — risk: reversible_write. Update a project."""
    return run_tool("n8n_project_update", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /projects/{projectId} — risk: destructive. Delete a project (refuses if non-empty without confirmation)."""
    return run_tool("n8n_project_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def user_list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /projects/{projectId}/users — risk: read_only. List project members."""
    return run_tool("n8n_project_user_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def user_add(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /projects/{projectId}/users — risk: production_impact. Add member(s) to a project (access change)."""
    return run_tool("n8n_project_user_add", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def user_remove(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /projects/{projectId}/users/{userId} — risk: destructive. Remove a member from a project."""
    return run_tool("n8n_project_user_remove", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def user_update_role(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PATCH /projects/{projectId}/users/{userId} — risk: production_impact. Change a member's project role."""
    return run_tool("n8n_project_user_update_role", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
