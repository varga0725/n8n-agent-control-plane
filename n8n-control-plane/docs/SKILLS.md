# Skills

Eleven agent skills, each a `skills/<name>/SKILL.md`. They are intentionally
split by domain (no monolithic `n8n-admin`) so an agent loads only what's
relevant and the risk surface stays legible.

| Skill | Covers | Key tools / operations |
|-------|--------|------------------------|
| `n8n-discovery` | capability discovery | `n8n_discover_capabilities` |
| `n8n-workflows` | workflow lifecycle | list/get/create/update/activate/archive/transfer/delete, `safe_workflow_deploy` |
| `n8n-executions` | runs & failures | list/get/retry/stop/delete, `execution_triage`, `failed_execution_recovery` |
| `n8n-credentials` | credentials | list/get/schema/create/update/test/transfer/delete, `credential_validation` |
| `n8n-users` | users & global roles | list/get/create/update_role/delete |
| `n8n-projects` | projects & membership | create/update/delete + members, `project_bootstrap` |
| `n8n-data-tables` | data tables | tables, rows (insert/update/upsert/delete), columns |
| `n8n-organization` | tags, folders, variables | create/list/update/delete each |
| `n8n-security` | audit & git | `n8n_audit_generate`, `security_review`, `source_control_sync` |
| `n8n-packages` | community + beta packages | install/list/update/uninstall, export/import |
| `n8n-operations` | high-level flows | all 12 operations |

## How skills, tools and operations relate
- A **skill** is the instruction layer an agent reads to decide *what to do and
  what's forbidden*.
- A **primitive tool** (`n8n_<domain>_<action>`) is one fixed API endpoint.
- An **operation** composes tools into a safe multi-step flow.

Companion skill: **n8n-workflow-builder** (separate) authors brand-new workflow
JSON from a description. The control plane then *deploys* that JSON via
`n8n-workflows` / `safe_workflow_deploy`. Build with one, operate with the other.

## Triggering guidance
Each skill's `description` is written to trigger on the user's intent even when
they don't name n8n explicitly (e.g. "retry the failed runs", "back up
everything", "who are the owners"). Start a session with `n8n-discovery`.
