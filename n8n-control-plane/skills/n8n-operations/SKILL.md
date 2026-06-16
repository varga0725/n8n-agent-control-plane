---
name: n8n-operations
description: >
  Run high-level, multi-step n8n control-plane operations that compose many API
  calls into one validated, audited, recoverable flow: safe workflow deploy,
  execution triage, failed-execution recovery, workflow backup/restore/clone,
  project bootstrap, credential validation, instance health report, security
  review, source-control sync, and disaster recovery. Use this skill WHENEVER the
  user's request is a workflow/process rather than a single API call — "deploy
  this safely", "why are things failing and fix the safe ones", "back up
  everything", "stand up a new project", "give me an instance health report".
  Prefer these operations over chaining primitives by hand.
version: 1.0.0
risk_level: mixed
---

# n8n Operations

The control plane's high-level layer. Each operation does the careful sequence a
senior operator would: discover → read → back up → validate → diff → show impact
→ act (gated) → verify → roll back on failure. They emit a step-by-step trace.

## When to use
- Any request that is really a procedure, not one endpoint call.
- When safety matters: deploys, recovery, bulk changes, environment setup.

## Operations
- `safe_workflow_deploy` — update a workflow with backup + diff + gated activate +
  rollback. The preferred way to change any workflow.
- `execution_triage` — group failures by workflow/node/root-cause, prioritize.
- `failed_execution_recovery` — classify failures; retry only idempotent-safe
  ones (payments/emails/etc. excluded), with confirmation.
- `workflow_backup` / `workflow_restore` — full JSON + metadata to/from disk.
- `workflow_clone` — copy a workflow (inactive), optionally into another project.
- `project_bootstrap` — create a project with users, folders, tags, variables.
- `credential_validation` — test credentials, find dependents, suggest fixes.
- `instance_health_report` — capabilities, workflow/exec stats, error rates,
  audit summary, insights, packages, maintenance suggestions.
- `security_review` — audit + access + secrets-hygiene + remediation roadmap.
- `source_control_sync` — preview → confirm → pull → report → health check.
- `disaster_recovery` — back up every workflow to disk for restore.

Run any operation:
```bash
python3 -m n8n_cp op <operation> --json '{...params...}'
python3 -m n8n_cp op <operation> --dry-run
python3 -m n8n_cp op <operation> --confirm <TOKEN>
```

## Inputs & output
Inputs are per-operation (see each above). Output is a result object with a
`steps` trace, `warnings`, `data`, and `error` — all redacted. When a gated step
needs approval, the relevant sub-result contains the `impact` + `confirmationToken`.

## Confirmation & safety
Operations never bypass gating: any destructive/production step inside them goes
through the same env-flag + operation-bound token machinery. Dry-run first when in
doubt; the operation reports exactly what it would do.

## Forbidden
- Bypassing backups in deploy/restore/delete flows.
- Auto-retrying non-idempotent executions.
- Acting on unconfirmed capabilities (always discover first).

## Examples
- "Deploy v2 of workflow 128 safely and activate it" →
  `safe_workflow_deploy --json '{"id":"128","workflow":{...},"activate":true}'`,
  show the diff, then supply the activation token.
- "Give me a health report" → `instance_health_report`.
- "Back up the whole instance" → `disaster_recovery`.
