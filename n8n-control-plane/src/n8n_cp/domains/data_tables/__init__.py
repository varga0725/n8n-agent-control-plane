"""Domain: data-tables. Thin wrappers over the tool registry."""
from __future__ import annotations
from typing import Optional
from ...tools import run_tool

TOOLS = [
    "n8n_data_table_list",
    "n8n_data_table_create",
    "n8n_data_table_get",
    "n8n_data_table_update",
    "n8n_data_table_delete",
    "n8n_data_table_row_list",
    "n8n_data_table_row_insert",
    "n8n_data_table_row_update",
    "n8n_data_table_row_upsert",
    "n8n_data_table_row_delete",
    "n8n_data_table_column_list",
    "n8n_data_table_column_create",
    "n8n_data_table_column_update",
    "n8n_data_table_column_delete",
]

def list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /data-tables — risk: read_only. List data tables."""
    return run_tool("n8n_data_table_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def create(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /data-tables — risk: reversible_write. Create a data table."""
    return run_tool("n8n_data_table_create", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def get(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /data-tables/{dataTableId} — risk: read_only. Get a data table."""
    return run_tool("n8n_data_table_get", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def update(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PATCH /data-tables/{dataTableId} — risk: reversible_write. Update a data table."""
    return run_tool("n8n_data_table_update", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /data-tables/{dataTableId} — risk: destructive. Delete a data table."""
    return run_tool("n8n_data_table_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def row_list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /data-tables/{dataTableId}/rows — risk: read_only. List rows (paginated)."""
    return run_tool("n8n_data_table_row_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def row_insert(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /data-tables/{dataTableId}/rows — risk: reversible_write. Insert rows."""
    return run_tool("n8n_data_table_row_insert", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def row_update(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PATCH /data-tables/{dataTableId}/rows/update — risk: reversible_write. Update rows by filter."""
    return run_tool("n8n_data_table_row_update", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def row_upsert(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /data-tables/{dataTableId}/rows/upsert — risk: reversible_write. Upsert rows."""
    return run_tool("n8n_data_table_row_upsert", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def row_delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /data-tables/{dataTableId}/rows/delete — risk: destructive. Delete rows by filter (empty filter refused)."""
    return run_tool("n8n_data_table_row_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def column_list(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """GET /data-tables/{dataTableId}/columns — risk: read_only. List columns."""
    return run_tool("n8n_data_table_column_list", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def column_create(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """POST /data-tables/{dataTableId}/columns — risk: reversible_write. Create a column."""
    return run_tool("n8n_data_table_column_create", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def column_update(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """PATCH /data-tables/{dataTableId}/columns/{columnId} — risk: reversible_write. Update a column."""
    return run_tool("n8n_data_table_column_update", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)

def column_delete(params: Optional[dict] = None, *, dry_run: bool = False,
       confirm_token: Optional[str] = None, **kw):
    """DELETE /data-tables/{dataTableId}/columns/{columnId} — risk: destructive. Delete a column (data loss warning)."""
    return run_tool("n8n_data_table_column_delete", {**(params or {}), **kw},
                    dry_run=dry_run, confirm_token=confirm_token)
