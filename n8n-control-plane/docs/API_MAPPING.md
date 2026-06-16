# API Mapping

Every n8n Public API (v1.1.1) endpoint, the primitive tool that calls it, the skill it belongs to, and its risk class. Generated from the endpoint registry (`src/n8n_cp/endpoints.py`) — the authoritative source.

## discover  (skill: `n8n-discovery`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/discover` | `n8n_discover_capabilities` | read_only |

## workflows  (skill: `n8n-workflows`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/workflows` | `n8n_workflow_list` | read_only |
| GET | `/workflows/{id}` | `n8n_workflow_get` | read_only |
| GET | `/workflows/{id}/{versionId}` | `n8n_workflow_get_version` | read_only |
| POST | `/workflows` | `n8n_workflow_create` | reversible_write |
| PUT | `/workflows/{id}` | `n8n_workflow_update` | reversible_write |
| POST | `/workflows/{id}/activate` | `n8n_workflow_activate` | production_impact |
| POST | `/workflows/{id}/deactivate` | `n8n_workflow_deactivate` | production_impact |
| POST | `/workflows/{id}/archive` | `n8n_workflow_archive` | reversible_write |
| POST | `/workflows/{id}/unarchive` | `n8n_workflow_unarchive` | reversible_write |
| PUT | `/workflows/{id}/transfer` | `n8n_workflow_transfer` | production_impact |
| GET | `/workflows/{id}/tags` | `n8n_workflow_get_tags` | read_only |
| PUT | `/workflows/{id}/tags` | `n8n_workflow_update_tags` | reversible_write |
| DELETE | `/workflows/{id}` | `n8n_workflow_delete` | destructive |

## executions  (skill: `n8n-executions`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/executions` | `n8n_execution_list` | read_only |
| GET | `/executions/{id}` | `n8n_execution_get` | read_only |
| POST | `/executions/{id}/retry` | `n8n_execution_retry` | production_impact |
| POST | `/executions/{id}/stop` | `n8n_execution_stop` | production_impact |
| POST | `/executions/stop` | `n8n_execution_stop_multiple` | production_impact |
| GET | `/executions/{id}/tags` | `n8n_execution_get_tags` | read_only |
| PUT | `/executions/{id}/tags` | `n8n_execution_update_tags` | reversible_write |
| DELETE | `/executions/{id}` | `n8n_execution_delete` | destructive |

## credentials  (skill: `n8n-credentials`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/credentials` | `n8n_credential_list` | read_only |
| GET | `/credentials/{id}` | `n8n_credential_get` | read_only |
| GET | `/credentials/schema/{credentialTypeName}` | `n8n_credential_get_schema` | read_only |
| POST | `/credentials` | `n8n_credential_create` | reversible_write |
| PATCH | `/credentials/{id}` | `n8n_credential_update` | reversible_write |
| POST | `/credentials/{id}/test` | `n8n_credential_test` | read_only |
| PUT | `/credentials/{id}/transfer` | `n8n_credential_transfer` | production_impact |
| DELETE | `/credentials/{id}` | `n8n_credential_delete` | destructive |

## tags  (skill: `n8n-organization`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| POST | `/tags` | `n8n_tag_create` | reversible_write |
| GET | `/tags` | `n8n_tag_list` | read_only |
| GET | `/tags/{id}` | `n8n_tag_get` | read_only |
| PUT | `/tags/{id}` | `n8n_tag_update` | reversible_write |
| DELETE | `/tags/{id}` | `n8n_tag_delete` | destructive |

## audit  (skill: `n8n-security`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| POST | `/audit` | `n8n_audit_generate` | read_only |

## source-control  (skill: `n8n-security`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| POST | `/source-control/pull` | `n8n_source_control_pull` | production_impact |

## variables  (skill: `n8n-organization`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/variables` | `n8n_variable_list` | read_only |
| POST | `/variables` | `n8n_variable_create` | reversible_write |
| PUT | `/variables/{id}` | `n8n_variable_update` | reversible_write |
| DELETE | `/variables/{id}` | `n8n_variable_delete` | destructive |

## projects  (skill: `n8n-projects`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/projects` | `n8n_project_list` | read_only |
| POST | `/projects` | `n8n_project_create` | reversible_write |
| PUT | `/projects/{projectId}` | `n8n_project_update` | reversible_write |
| DELETE | `/projects/{projectId}` | `n8n_project_delete` | destructive |
| GET | `/projects/{projectId}/users` | `n8n_project_user_list` | read_only |
| POST | `/projects/{projectId}/users` | `n8n_project_user_add` | production_impact |
| DELETE | `/projects/{projectId}/users/{userId}` | `n8n_project_user_remove` | destructive |
| PATCH | `/projects/{projectId}/users/{userId}` | `n8n_project_user_update_role` | production_impact |

## users  (skill: `n8n-users`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/users` | `n8n_user_list` | read_only |
| GET | `/users/{id}` | `n8n_user_get` | read_only |
| POST | `/users` | `n8n_user_create` | production_impact |
| PATCH | `/users/{id}/role` | `n8n_user_update_role` | production_impact |
| DELETE | `/users/{id}` | `n8n_user_delete` | destructive |

## folders  (skill: `n8n-organization`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/projects/{projectId}/folders` | `n8n_folder_list` | read_only |
| POST | `/projects/{projectId}/folders` | `n8n_folder_create` | reversible_write |
| GET | `/projects/{projectId}/folders/{folderId}` | `n8n_folder_get` | read_only |
| PATCH | `/projects/{projectId}/folders/{folderId}` | `n8n_folder_update` | reversible_write |
| DELETE | `/projects/{projectId}/folders/{folderId}` | `n8n_folder_delete` | destructive |

## data-tables  (skill: `n8n-data-tables`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/data-tables` | `n8n_data_table_list` | read_only |
| POST | `/data-tables` | `n8n_data_table_create` | reversible_write |
| GET | `/data-tables/{dataTableId}` | `n8n_data_table_get` | read_only |
| PATCH | `/data-tables/{dataTableId}` | `n8n_data_table_update` | reversible_write |
| DELETE | `/data-tables/{dataTableId}` | `n8n_data_table_delete` | destructive |
| GET | `/data-tables/{dataTableId}/rows` | `n8n_data_table_row_list` | read_only |
| POST | `/data-tables/{dataTableId}/rows` | `n8n_data_table_row_insert` | reversible_write |
| PATCH | `/data-tables/{dataTableId}/rows/update` | `n8n_data_table_row_update` | reversible_write |
| POST | `/data-tables/{dataTableId}/rows/upsert` | `n8n_data_table_row_upsert` | reversible_write |
| DELETE | `/data-tables/{dataTableId}/rows/delete` | `n8n_data_table_row_delete` | destructive |
| GET | `/data-tables/{dataTableId}/columns` | `n8n_data_table_column_list` | read_only |
| POST | `/data-tables/{dataTableId}/columns` | `n8n_data_table_column_create` | reversible_write |
| PATCH | `/data-tables/{dataTableId}/columns/{columnId}` | `n8n_data_table_column_update` | reversible_write |
| DELETE | `/data-tables/{dataTableId}/columns/{columnId}` | `n8n_data_table_column_delete` | destructive |

## insights  (skill: `n8n-operations`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/insights/summary` | `n8n_insights_summary` | read_only |

## community-packages  (skill: `n8n-packages`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| GET | `/community-packages` | `n8n_community_package_list` | read_only |
| POST | `/community-packages` | `n8n_community_package_install` | production_impact |
| PATCH | `/community-packages/{name}` | `n8n_community_package_update` | production_impact |
| DELETE | `/community-packages/{name}` | `n8n_community_package_uninstall` | destructive |

## n8n-packages  (skill: `n8n-packages`)

| Method | Path | Tool | Risk |
|--------|------|------|------|
| POST | `/n8n-packages/export` | `n8n_package_export` _(beta)_ | reversible_write |
| POST | `/n8n-packages/import` | `n8n_package_import` _(beta)_ | production_impact |

**Total endpoints/tools: 80** across 15 domains.