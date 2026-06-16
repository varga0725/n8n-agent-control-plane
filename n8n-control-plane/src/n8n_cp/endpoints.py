"""The endpoint/tool registry — the single source of truth mapping every n8n
Public API (v1.1.1) endpoint to a fixed, named, risk-classified primitive tool.

This is deliberately *data-driven*. There is no free-form "method + path + body"
tool (explicitly forbidden by the spec): an agent can only invoke a named tool
whose method, path template and risk level are fixed here. Adding a new endpoint
means adding a row, not writing imperative code.

Risk levels follow the project specification's classification (section 8).
``pre_checks`` are named safety hooks resolved by tools.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .core.risk import RiskLevel

RO = RiskLevel.READ_ONLY
RW = RiskLevel.REVERSIBLE_WRITE
PI = RiskLevel.PRODUCTION_IMPACT
DE = RiskLevel.DESTRUCTIVE


@dataclass(frozen=True)
class ToolSpec:
    name: str
    method: str
    path: str                       # may contain {placeholders}
    risk: RiskLevel
    domain: str
    resource_type: str
    path_params: tuple = ()          # required path params (from {placeholders})
    body_required: bool = False
    is_list: bool = False            # cursor-paginated list endpoint
    pre_checks: tuple = ()           # named hooks, see tools.py
    beta: bool = False
    summary: str = ""

    @property
    def resource_id_param(self) -> Optional[str]:
        return self.path_params[-1] if self.path_params else None


def _spec(*a, **k) -> ToolSpec:
    return ToolSpec(*a, **k)


_SPECS: list[ToolSpec] = [
    # ---- discovery ------------------------------------------------------
    _spec("n8n_discover_capabilities", "GET", "/discover", RO, "discover",
          "capabilities", summary="Discover which API features this instance supports."),

    # ---- workflows ------------------------------------------------------
    _spec("n8n_workflow_list", "GET", "/workflows", RO, "workflows", "workflow",
          is_list=True, summary="List/search workflows (filterable, paginated)."),
    _spec("n8n_workflow_get", "GET", "/workflows/{id}", RO, "workflows", "workflow",
          path_params=("id",), summary="Get a workflow's full structure."),
    _spec("n8n_workflow_get_version", "GET", "/workflows/{id}/{versionId}", RO,
          "workflows", "workflow", path_params=("id", "versionId"),
          summary="Get a specific workflow version."),
    _spec("n8n_workflow_create", "POST", "/workflows", RW, "workflows", "workflow",
          body_required=True, pre_checks=("validate_workflow_body", "force_inactive_create"),
          summary="Create a workflow (always inactive on create)."),
    _spec("n8n_workflow_update", "PUT", "/workflows/{id}", RW, "workflows", "workflow",
          path_params=("id",), body_required=True,
          pre_checks=("validate_workflow_body", "dynamic_active_risk"),
          summary="Update a workflow (escalates to production-impact if active)."),
    _spec("n8n_workflow_activate", "POST", "/workflows/{id}/activate", PI,
          "workflows", "workflow", path_params=("id",),
          summary="Activate a workflow (turns on its triggers)."),
    _spec("n8n_workflow_deactivate", "POST", "/workflows/{id}/deactivate", PI,
          "workflows", "workflow", path_params=("id",),
          summary="Deactivate a workflow."),
    _spec("n8n_workflow_archive", "POST", "/workflows/{id}/archive", RW,
          "workflows", "workflow", path_params=("id",), summary="Archive a workflow."),
    _spec("n8n_workflow_unarchive", "POST", "/workflows/{id}/unarchive", RW,
          "workflows", "workflow", path_params=("id",), summary="Restore from archive."),
    _spec("n8n_workflow_transfer", "PUT", "/workflows/{id}/transfer", PI,
          "workflows", "workflow", path_params=("id",), body_required=True,
          summary="Move a workflow to another project."),
    _spec("n8n_workflow_get_tags", "GET", "/workflows/{id}/tags", RO,
          "workflows", "workflow", path_params=("id",), summary="Get a workflow's tags."),
    _spec("n8n_workflow_update_tags", "PUT", "/workflows/{id}/tags", RW,
          "workflows", "workflow", path_params=("id",), body_required=True,
          summary="Set a workflow's tags (array of tag IDs)."),
    _spec("n8n_workflow_delete", "DELETE", "/workflows/{id}", DE,
          "workflows", "workflow", path_params=("id",),
          pre_checks=("require_backup",), summary="Delete a workflow (destructive)."),

    # ---- executions -----------------------------------------------------
    _spec("n8n_execution_list", "GET", "/executions", RO, "executions", "execution",
          is_list=True, pre_checks=("default_execution_window",),
          summary="List executions (defaults to a bounded window, paginated)."),
    _spec("n8n_execution_get", "GET", "/executions/{id}", RO, "executions",
          "execution", path_params=("id",), summary="Get one execution (optionally with data)."),
    _spec("n8n_execution_retry", "POST", "/executions/{id}/retry", PI,
          "executions", "execution", path_params=("id",),
          pre_checks=("idempotency_check",),
          summary="Retry a failed execution (blocked for non-idempotent side effects)."),
    _spec("n8n_execution_stop", "POST", "/executions/{id}/stop", PI,
          "executions", "execution", path_params=("id",), summary="Stop a running execution."),
    _spec("n8n_execution_stop_multiple", "POST", "/executions/stop", PI,
          "executions", "execution", body_required=True,
          pre_checks=("bulk_stop_preview",), summary="Stop multiple executions."),
    _spec("n8n_execution_get_tags", "GET", "/executions/{id}/tags", RO,
          "executions", "execution", path_params=("id",), summary="Get execution tags."),
    _spec("n8n_execution_update_tags", "PUT", "/executions/{id}/tags", RW,
          "executions", "execution", path_params=("id",), body_required=True,
          summary="Set execution tags."),
    _spec("n8n_execution_delete", "DELETE", "/executions/{id}", DE,
          "executions", "execution", path_params=("id",), summary="Delete an execution record."),

    # ---- credentials ----------------------------------------------------
    _spec("n8n_credential_list", "GET", "/credentials", RO, "credentials",
          "credential", is_list=True, summary="List credential metadata (never secrets)."),
    _spec("n8n_credential_get", "GET", "/credentials/{id}", RO, "credentials",
          "credential", path_params=("id",), summary="Get credential metadata."),
    _spec("n8n_credential_get_schema", "GET", "/credentials/schema/{credentialTypeName}",
          RO, "credentials", "credential", path_params=("credentialTypeName",),
          summary="Get the required fields for a credential type."),
    _spec("n8n_credential_create", "POST", "/credentials", RW, "credentials",
          "credential", body_required=True, summary="Create a credential."),
    _spec("n8n_credential_update", "PATCH", "/credentials/{id}", RW, "credentials",
          "credential", path_params=("id",), body_required=True, summary="Update a credential."),
    _spec("n8n_credential_test", "POST", "/credentials/{id}/test", RO, "credentials",
          "credential", path_params=("id",), summary="Test a credential (result is redacted)."),
    _spec("n8n_credential_transfer", "PUT", "/credentials/{id}/transfer", PI,
          "credentials", "credential", path_params=("id",), body_required=True,
          summary="Move a credential to another project."),
    _spec("n8n_credential_delete", "DELETE", "/credentials/{id}", DE, "credentials",
          "credential", path_params=("id",), pre_checks=("credential_usage_check",),
          summary="Delete a credential (checks for workflows using it)."),

    # ---- tags -----------------------------------------------------------
    _spec("n8n_tag_create", "POST", "/tags", RW, "tags", "tag", body_required=True,
          pre_checks=("tag_dup_check",), summary="Create a tag (dedup by name)."),
    _spec("n8n_tag_list", "GET", "/tags", RO, "tags", "tag", is_list=True, summary="List tags."),
    _spec("n8n_tag_get", "GET", "/tags/{id}", RO, "tags", "tag", path_params=("id",),
          summary="Get a tag."),
    _spec("n8n_tag_update", "PUT", "/tags/{id}", RW, "tags", "tag", path_params=("id",),
          body_required=True, summary="Rename a tag."),
    _spec("n8n_tag_delete", "DELETE", "/tags/{id}", DE, "tags", "tag", path_params=("id",),
          summary="Delete a tag (destructive)."),

    # ---- audit ----------------------------------------------------------
    _spec("n8n_audit_generate", "POST", "/audit", RO, "audit", "audit",
          summary="Run an n8n security audit and return findings."),

    # ---- source control -------------------------------------------------
    _spec("n8n_source_control_pull", "POST", "/source-control/pull", PI,
          "source-control", "source-control", pre_checks=("require_dry_run_first",),
          summary="Pull from the connected git remote (production-impact)."),

    # ---- variables ------------------------------------------------------
    _spec("n8n_variable_list", "GET", "/variables", RO, "variables", "variable",
          is_list=True, summary="List variables."),
    _spec("n8n_variable_create", "POST", "/variables", RW, "variables", "variable",
          body_required=True, pre_checks=("warn_secret_in_variable",),
          summary="Create a variable (warns if value looks secret)."),
    _spec("n8n_variable_update", "PUT", "/variables/{id}", RW, "variables", "variable",
          path_params=("id",), body_required=True, summary="Update a variable."),
    _spec("n8n_variable_delete", "DELETE", "/variables/{id}", DE, "variables",
          "variable", path_params=("id",), summary="Delete a variable (destructive)."),

    # ---- projects -------------------------------------------------------
    _spec("n8n_project_list", "GET", "/projects", RO, "projects", "project",
          is_list=True, summary="List projects."),
    _spec("n8n_project_create", "POST", "/projects", RW, "projects", "project",
          body_required=True, summary="Create a project."),
    _spec("n8n_project_update", "PUT", "/projects/{projectId}", RW, "projects",
          "project", path_params=("projectId",), body_required=True, summary="Update a project."),
    _spec("n8n_project_delete", "DELETE", "/projects/{projectId}", DE, "projects",
          "project", path_params=("projectId",), pre_checks=("project_inventory_check",),
          summary="Delete a project (refuses if non-empty without confirmation)."),
    _spec("n8n_project_user_list", "GET", "/projects/{projectId}/users", RO,
          "projects", "project-user", path_params=("projectId",), summary="List project members."),
    _spec("n8n_project_user_add", "POST", "/projects/{projectId}/users", PI,
          "projects", "project-user", path_params=("projectId",), body_required=True,
          summary="Add member(s) to a project (access change)."),
    _spec("n8n_project_user_remove", "DELETE", "/projects/{projectId}/users/{userId}",
          DE, "projects", "project-user", path_params=("projectId", "userId"),
          summary="Remove a member from a project."),
    _spec("n8n_project_user_update_role", "PATCH", "/projects/{projectId}/users/{userId}",
          PI, "projects", "project-user", path_params=("projectId", "userId"),
          body_required=True, summary="Change a member's project role."),

    # ---- users ----------------------------------------------------------
    _spec("n8n_user_list", "GET", "/users", RO, "users", "user", is_list=True,
          summary="List users."),
    _spec("n8n_user_get", "GET", "/users/{id}", RO, "users", "user", path_params=("id",),
          summary="Get a user by id or email."),
    _spec("n8n_user_create", "POST", "/users", PI, "users", "user", body_required=True,
          pre_checks=("email_dup_check",), summary="Create user(s) (access change; dedup emails)."),
    _spec("n8n_user_update_role", "PATCH", "/users/{id}/role", PI, "users", "user",
          path_params=("id",), body_required=True, pre_checks=("owner_role_guard",),
          summary="Change a user's global role (owner changes are high risk)."),
    _spec("n8n_user_delete", "DELETE", "/users/{id}", DE, "users", "user",
          path_params=("id",), pre_checks=("owner_delete_guard",),
          summary="Delete a user (destructive; owner deletion guarded)."),

    # ---- folders --------------------------------------------------------
    _spec("n8n_folder_list", "GET", "/projects/{projectId}/folders", RO, "folders",
          "folder", path_params=("projectId",), is_list=True, summary="List folders."),
    _spec("n8n_folder_create", "POST", "/projects/{projectId}/folders", RW, "folders",
          "folder", path_params=("projectId",), body_required=True, summary="Create a folder."),
    _spec("n8n_folder_get", "GET", "/projects/{projectId}/folders/{folderId}", RO,
          "folders", "folder", path_params=("projectId", "folderId"), summary="Get folder details."),
    _spec("n8n_folder_update", "PATCH", "/projects/{projectId}/folders/{folderId}", RW,
          "folders", "folder", path_params=("projectId", "folderId"), body_required=True,
          summary="Update a folder."),
    _spec("n8n_folder_delete", "DELETE", "/projects/{projectId}/folders/{folderId}", DE,
          "folders", "folder", path_params=("projectId", "folderId"),
          pre_checks=("folder_contents_check",), summary="Delete a folder (checks contents)."),

    # ---- data tables ----------------------------------------------------
    _spec("n8n_data_table_list", "GET", "/data-tables", RO, "data-tables", "data-table",
          is_list=True, summary="List data tables."),
    _spec("n8n_data_table_create", "POST", "/data-tables", RW, "data-tables", "data-table",
          body_required=True, summary="Create a data table."),
    _spec("n8n_data_table_get", "GET", "/data-tables/{dataTableId}", RO, "data-tables",
          "data-table", path_params=("dataTableId",), summary="Get a data table."),
    _spec("n8n_data_table_update", "PATCH", "/data-tables/{dataTableId}", RW,
          "data-tables", "data-table", path_params=("dataTableId",), body_required=True,
          summary="Update a data table."),
    _spec("n8n_data_table_delete", "DELETE", "/data-tables/{dataTableId}", DE,
          "data-tables", "data-table", path_params=("dataTableId",), summary="Delete a data table."),
    _spec("n8n_data_table_row_list", "GET", "/data-tables/{dataTableId}/rows", RO,
          "data-tables", "data-table-row", path_params=("dataTableId",), is_list=True,
          summary="List rows (paginated)."),
    _spec("n8n_data_table_row_insert", "POST", "/data-tables/{dataTableId}/rows", RW,
          "data-tables", "data-table-row", path_params=("dataTableId",), body_required=True,
          summary="Insert rows."),
    _spec("n8n_data_table_row_update", "PATCH", "/data-tables/{dataTableId}/rows/update", RW,
          "data-tables", "data-table-row", path_params=("dataTableId",), body_required=True,
          pre_checks=("require_update_filter",), summary="Update rows by filter."),
    _spec("n8n_data_table_row_upsert", "POST", "/data-tables/{dataTableId}/rows/upsert", RW,
          "data-tables", "data-table-row", path_params=("dataTableId",), body_required=True,
          summary="Upsert rows."),
    _spec("n8n_data_table_row_delete", "DELETE", "/data-tables/{dataTableId}/rows/delete", DE,
          "data-tables", "data-table-row", path_params=("dataTableId",), body_required=True,
          pre_checks=("reject_empty_delete_filter", "row_delete_preview"),
          summary="Delete rows by filter (empty filter refused)."),
    _spec("n8n_data_table_column_list", "GET", "/data-tables/{dataTableId}/columns", RO,
          "data-tables", "data-table-column", path_params=("dataTableId",),
          summary="List columns."),
    _spec("n8n_data_table_column_create", "POST", "/data-tables/{dataTableId}/columns", RW,
          "data-tables", "data-table-column", path_params=("dataTableId",), body_required=True,
          summary="Create a column."),
    _spec("n8n_data_table_column_update", "PATCH",
          "/data-tables/{dataTableId}/columns/{columnId}", RW, "data-tables",
          "data-table-column", path_params=("dataTableId", "columnId"), body_required=True,
          summary="Update a column."),
    _spec("n8n_data_table_column_delete", "DELETE",
          "/data-tables/{dataTableId}/columns/{columnId}", DE, "data-tables",
          "data-table-column", path_params=("dataTableId", "columnId"),
          pre_checks=("column_delete_warning",), summary="Delete a column (data loss warning)."),

    # ---- insights -------------------------------------------------------
    _spec("n8n_insights_summary", "GET", "/insights/summary", RO, "insights",
          "insights", summary="Performance / execution insights summary."),

    # ---- community packages --------------------------------------------
    _spec("n8n_community_package_list", "GET", "/community-packages", RO,
          "community-packages", "community-package", is_list=True,
          summary="List installed community packages."),
    _spec("n8n_community_package_install", "POST", "/community-packages", PI,
          "community-packages", "community-package", body_required=True,
          pre_checks=("validate_package_ref",), summary="Install a community package."),
    _spec("n8n_community_package_update", "PATCH", "/community-packages/{name}", PI,
          "community-packages", "community-package", path_params=("name",),
          summary="Update a community package."),
    _spec("n8n_community_package_uninstall", "DELETE", "/community-packages/{name}", DE,
          "community-packages", "community-package", path_params=("name",),
          pre_checks=("package_usage_check",), summary="Uninstall a community package."),

    # ---- n8n packages (beta) -------------------------------------------
    _spec("n8n_package_export", "POST", "/n8n-packages/export", RW, "n8n-packages",
          "n8n-package", body_required=True, beta=True,
          summary="Export workflows to n8n package format (beta)."),
    _spec("n8n_package_import", "POST", "/n8n-packages/import", PI, "n8n-packages",
          "n8n-package", body_required=True, beta=True,
          pre_checks=("validate_import_plan",), summary="Import an n8n package (beta)."),
]

REGISTRY: dict[str, ToolSpec] = {s.name: s for s in _SPECS}


def by_domain() -> dict[str, list[ToolSpec]]:
    out: dict[str, list[ToolSpec]] = {}
    for s in _SPECS:
        out.setdefault(s.domain, []).append(s)
    return out


def get(name: str) -> Optional[ToolSpec]:
    return REGISTRY.get(name)
