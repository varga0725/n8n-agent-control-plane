"""Domain: folders. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_folder_list",
    "n8n_folder_create",
    "n8n_folder_get",
    "n8n_folder_update",
    "n8n_folder_delete",
]

def list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /projects/{projectId}/folders — risk: read_only. List folders."""
    return run_tool("n8n_folder_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def create(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /projects/{projectId}/folders — risk: reversible_write. Create a folder."""
    return run_tool("n8n_folder_create", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /projects/{projectId}/folders/{folderId} — risk: read_only. Get folder details."""
    return run_tool("n8n_folder_get", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PATCH /projects/{projectId}/folders/{folderId} — risk: reversible_write. Update a folder."""
    return run_tool("n8n_folder_update", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /projects/{projectId}/folders/{folderId} — risk: destructive. Delete a folder (checks contents)."""
    return run_tool("n8n_folder_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
