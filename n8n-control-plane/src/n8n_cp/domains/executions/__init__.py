"""Domain: executions. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_execution_list",
    "n8n_execution_get",
    "n8n_execution_retry",
    "n8n_execution_stop",
    "n8n_execution_stop_multiple",
    "n8n_execution_get_tags",
    "n8n_execution_update_tags",
    "n8n_execution_delete",
]

def list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /executions — risk: read_only. List executions (defaults to a bounded window, paginated)."""
    return run_tool("n8n_execution_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /executions/{id} — risk: read_only. Get one execution (optionally with data)."""
    return run_tool("n8n_execution_get", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def retry(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /executions/{id}/retry — risk: production_impact. Retry a failed execution (blocked for non-idempotent side effects)."""
    return run_tool("n8n_execution_retry", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def stop(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /executions/{id}/stop — risk: production_impact. Stop a running execution."""
    return run_tool("n8n_execution_stop", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def stop_multiple(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /executions/stop — risk: production_impact. Stop multiple executions."""
    return run_tool("n8n_execution_stop_multiple", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get_tags(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /executions/{id}/tags — risk: read_only. Get execution tags."""
    return run_tool("n8n_execution_get_tags", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update_tags(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PUT /executions/{id}/tags — risk: reversible_write. Set execution tags."""
    return run_tool("n8n_execution_update_tags", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /executions/{id} — risk: destructive. Delete an execution record."""
    return run_tool("n8n_execution_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
