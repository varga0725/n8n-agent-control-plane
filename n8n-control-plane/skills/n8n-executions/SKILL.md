---
name: n8n-executions
description: >
  Inspect, filter, stop, retry, tag and delete n8n workflow executions safely.
  Use this skill WHENEVER the user asks about runs, failures, or execution
  history — "why did the sync fail", "show failed executions today", "stop that
  stuck run", "retry the failed ones", "what's the error rate". Never auto-retry
  executions with non-idempotent side effects (payments, emails, CRM/DB writes,
  orders). Never pull the entire execution history — always filter or bound the
  window.
version: 1.0.0
risk_level: mixed
---

# n8n Executions

Executions are where production reality shows up. This skill reads run history,
diagnoses failures, and — carefully — stops or retries runs.

## When to use
- Listing/filtering executions; inspecting a specific run's data and failing node.
- Stopping a running (or many running) execution(s).
- Retrying a failed execution **only when it is idempotent-safe**.
- Triage and recovery (delegate to the operations: `execution_triage`,
  `failed_execution_recovery`).

## When NOT to use
- Changing the workflow itself → **n8n-workflows**.
- Triggering a new run on demand — the Public API does not run workflows; use the
  workflow's webhook/schedule trigger instead.

## Tools
Read: `n8n_execution_list`, `n8n_execution_get`, `n8n_execution_get_tags`.
Production-impact: `n8n_execution_retry`, `n8n_execution_stop`,
`n8n_execution_stop_multiple`.
Reversible: `n8n_execution_update_tags`.
Destructive: `n8n_execution_delete`.
Operations: `execution_triage`, `failed_execution_recovery`.

## Inputs & data-volume rules
- `n8n_execution_list` defaults to a bounded window (limit 20) when no filter is
  given. Always pass `workflowId`, `status`, and/or `startedAfter` to target.
  "List the executions" must never auto-download the full history.
- `n8n_execution_get` with `includeData=true` for the failing node + error.

## Retry safety (critical)
Before any retry, the idempotency check inspects the executed nodes:
- **Auto retry-safe**: timeouts, transient network errors, HTTP 429/502/503/504,
  temporary upstream failures.
- **Manual review**: credential errors, invalid input, expression errors, schema
  mismatch, permission errors, node misconfiguration.
- **Never auto-retry**: payments, billing, sending email/messages, CRM/DB writes,
  file deletion, non-idempotent external API calls, order/booking creation.

`n8n_execution_retry` refuses outright when side effects look non-idempotent.

## Confirmation rules
Retry, stop, and bulk-stop are production-impact: require the env flag and an
operation-bound confirmation token. Bulk stop first previews the affected count.

## Forbidden
- Auto-retrying non-idempotent executions.
- Logging raw execution data containing secrets/PII (redaction is on by default;
  keep `N8N_REDACT_EXECUTION_DATA=true`).
- Unbounded history pulls.

## Examples
- "Why is the Shopify sync failing?" → `execution_triage --json '{"workflowId":"77"}'`
  → group by root cause, show the failing node + message.
- "Retry the transient failures from this morning, nothing risky" →
  `failed_execution_recovery --json '{"workflowId":"77","auto":true}'` with a
  confirmation token; payments/emails are excluded automatically.
- "Stop run 9001" → `n8n_execution_stop --param id=9001 --dry-run` then confirm.
