"""Domain: credentials. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_credential_list",
    "n8n_credential_get",
    "n8n_credential_get_schema",
    "n8n_credential_create",
    "n8n_credential_update",
    "n8n_credential_test",
    "n8n_credential_transfer",
    "n8n_credential_delete",
]

def list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /credentials — risk: read_only. List credential metadata (never secrets)."""
    return run_tool("n8n_credential_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /credentials/{id} — risk: read_only. Get credential metadata."""
    return run_tool("n8n_credential_get", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get_schema(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /credentials/schema/{credentialTypeName} — risk: read_only. Get the required fields for a credential type."""
    return run_tool("n8n_credential_get_schema", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def create(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /credentials — risk: reversible_write. Create a credential."""
    return run_tool("n8n_credential_create", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PATCH /credentials/{id} — risk: reversible_write. Update a credential."""
    return run_tool("n8n_credential_update", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def test(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /credentials/{id}/test — risk: read_only. Test a credential (result is redacted)."""
    return run_tool("n8n_credential_test", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def transfer(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PUT /credentials/{id}/transfer — risk: production_impact. Move a credential to another project."""
    return run_tool("n8n_credential_transfer", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /credentials/{id} — risk: destructive. Delete a credential (checks for workflows using it)."""
    return run_tool("n8n_credential_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
