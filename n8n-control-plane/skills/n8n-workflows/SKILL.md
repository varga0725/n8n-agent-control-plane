---
name: n8n-workflows
description: >
  Safely create, read, search, version, update, activate, deactivate, archive,
  transfer, tag and delete n8n workflows through the Public API. Use this skill
  WHENEVER the user wants to manage existing workflows on an n8n instance —
  "deploy this workflow", "activate the invoice flow", "what changed in workflow
  128", "archive old workflows", "move this workflow to another project",
  "delete that workflow" — i.e. operations ON the instance, not authoring JSON
  from scratch. For authoring brand-new workflow JSON from a description, use the
  separate n8n-workflow-builder skill, then deploy it here. Never silently modify
  an active workflow; never delete without a backup.
version: 1.0.0
risk_level: mixed
---

# n8n Workflows

This skill manages the lifecycle of workflows on a live instance. The golden
rule: changes to live (active) workflows are production-impact and must be
backed up, diffed, shown, and confirmed — never applied silently.

## When to use
- Listing/searching/inspecting workflows or specific versions.
- Updating, activating, deactivating, archiving/unarchiving, transferring, tagging.
- Deleting a workflow (with backup + confirmation).
- Deploying a new or revised workflow body onto the instance.

## When NOT to use
- Designing workflow JSON from a natural-language description → use
  **n8n-workflow-builder**, then deploy the result here.
- Reading execution history → use **n8n-executions**.

## Tools
Read: `n8n_workflow_list`, `n8n_workflow_get`, `n8n_workflow_get_version`,
`n8n_workflow_get_tags`.
Write (reversible): `n8n_workflow_create` (always inactive), `n8n_workflow_update`
(escalates to production-impact if the target is active), `n8n_workflow_archive`,
`n8n_workflow_unarchive`, `n8n_workflow_update_tags`.
Production-impact: `n8n_workflow_activate`, `n8n_workflow_deactivate`,
`n8n_workflow_transfer`.
Destructive: `n8n_workflow_delete`.
Operation: `safe_workflow_deploy` (the preferred path for any update).

## Inputs
- IDs are required for get/update/activate/etc. If unsure of the ID, **list or
  search first** — never guess.
- Update/create take a workflow body with `name`, `nodes`, `connections`,
  `settings` (read-only fields like `active`/`id`/`tags` are stripped).

## Expected output
Standard envelope. For blocked production/destructive steps you receive an
`impact` summary plus a `confirmationToken` — show the impact to the user and
re-call with the token.

## Mandatory pre-checks before any update (use safe_workflow_deploy)
1. fetch current workflow  2. take a backup  3. validate new body
4. node + connection diff  5. check credential references  6. check active status
7. summarize impact  8. update  9. read back + validate  10. activate only with a
separate confirmation  11. roll back from backup on failure.

```bash
python3 -m n8n_cp op safe_workflow_deploy --json '{"id":"128","workflow":{...},"activate":false}'
```

## Confirmation rules
- Updating an ACTIVE workflow, activating, deactivating, transferring, deleting →
  require an explicit, operation-bound confirmation token (and the matching env
  flag). A generic "yes" never authorizes a different operation.

## Forbidden
- Silently modifying an active workflow.
- Deleting without a verified backup/export.
- Activating in production without explicit approval.
- Sending read-only fields (`active`, `tags`, `id`) in a create/update body.

## Error handling
Errors come back normalized (`validation_error`, `not_found`, `permission_error`,
…) — never raw HTML/stack traces. `404` → re-list to confirm the ID. `400` →
inspect `error.details` for the schema problem.

## Examples
- "Deploy the new version of workflow 128 but don't turn it on" →
  `safe_workflow_deploy` with `activate:false`, show the diff, confirm if active.
- "Archive every inactive workflow older than a year" → `n8n_workflow_list`,
  filter client-side, then `n8n_workflow_archive` each (reversible).
- "Delete workflow 200" → `n8n_workflow_delete --dry-run` to preview impact +
  get token → back it up → re-run with the token.
