"""Domain: workflows. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_workflow_list",
    "n8n_workflow_get",
    "n8n_workflow_get_version",
    "n8n_workflow_create",
    "n8n_workflow_update",
    "n8n_workflow_activate",
    "n8n_workflow_deactivate",
    "n8n_workflow_archive",
    "n8n_workflow_unarchive",
    "n8n_workflow_transfer",
    "n8n_workflow_get_tags",
    "n8n_workflow_update_tags",
    "n8n_workflow_delete",
]

def list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /workflows — risk: read_only. List/search workflows (filterable, paginated)."""
    return run_tool("n8n_workflow_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /workflows/{id} — risk: read_only. Get a workflow's full structure."""
    return run_tool("n8n_workflow_get", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get_version(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /workflows/{id}/{versionId} — risk: read_only. Get a specific workflow version."""
    return run_tool("n8n_workflow_get_version", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def create(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /workflows — risk: reversible_write. Create a workflow (always inactive on create)."""
    return run_tool("n8n_workflow_create", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PUT /workflows/{id} — risk: reversible_write. Update a workflow (escalates to production-impact if active)."""
    return run_tool("n8n_workflow_update", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def activate(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /workflows/{id}/activate — risk: production_impact. Activate a workflow (turns on its triggers)."""
    return run_tool("n8n_workflow_activate", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def deactivate(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /workflows/{id}/deactivate — risk: production_impact. Deactivate a workflow."""
    return run_tool("n8n_workflow_deactivate", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def archive(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /workflows/{id}/archive — risk: reversible_write. Archive a workflow."""
    return run_tool("n8n_workflow_archive", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def unarchive(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /workflows/{id}/unarchive — risk: reversible_write. Restore from archive."""
    return run_tool("n8n_workflow_unarchive", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def transfer(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PUT /workflows/{id}/transfer — risk: production_impact. Move a workflow to another project."""
    return run_tool("n8n_workflow_transfer", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get_tags(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /workflows/{id}/tags — risk: read_only. Get a workflow's tags."""
    return run_tool("n8n_workflow_get_tags", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update_tags(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PUT /workflows/{id}/tags — risk: reversible_write. Set a workflow's tags (array of tag IDs)."""
    return run_tool("n8n_workflow_update_tags", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /workflows/{id} — risk: destructive. Delete a workflow (destructive)."""
    return run_tool("n8n_workflow_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
