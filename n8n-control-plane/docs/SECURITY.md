# Security Model

## Principles
1. **Least privilege by default** — read-only + reversible-write only, until the
   operator opts into more via `ALLOW_*` env flags.
2. **Confirmation for irreversible/impactful actions** — operation-bound,
   short-lived tokens; a generic "yes" never carries over to a different action.
3. **Secrets stay secret** — recursive redaction; the API key is never logged.
4. **Auditability** — every write produces a structured, redacted audit record.
5. **Capability-first** — never call features the instance doesn't expose.

## API key handling
- Read only from `N8N_API_KEY`. Sent solely as the `X-N8N-API-KEY` header.
- Never written to logs, audit records, error output, or backups.
- Not parsed from files by this package (no accidental repo capture).

## Secret redaction
`core/redaction.py` masks values whose key matches any of: password, passphrase,
apiKey/api_key, token, accessToken, refreshToken, secret, clientSecret,
privateKey, authorization, cookie, session, webhookSecret, and n8n `credentials`
blobs. Redaction is recursive over objects and arrays. The only allowlisted
key is our own `confirmationToken` (a non-secret approval handle).
Credential `test` results and execution data are redacted too
(`N8N_REDACT_EXECUTION_DATA`).

## Risk classification & gating
Four levels (`core/risk.py`, mirrored in `policies/permissions.yaml`):
- `read_only` → auto.
- `reversible_write` → auto after validation + audit.
- `production_impact` → needs `N8N_ALLOW_PRODUCTION_WRITES` + confirmation.
- `destructive` → needs `N8N_ALLOW_DESTRUCTIVE` + confirmation.

`n8n_workflow_update` auto-escalates to `production_impact` when the target
workflow is active.

## Hard safety rules (refused even with a token)
- Data Table row delete with an empty/absent filter.
- Data Table row update without a filter.
- Auto-retry of executions with non-idempotent side effects (payments, emails,
  CRM/DB writes, orders, file deletes).
- Beta `n8n-packages` use without confirmed capability.

## Threat notes
- No free-form HTTP tool exists; the registry fixes every method/path, so prompt
  injection cannot construct an arbitrary request.
- Confirmation tokens are HMAC-signed with a per-process secret and bound to
  (operation, resourceId, expiry); they can't be forged or replayed elsewhere.
- Backups strip read-only fields and redact defensively; they store credential
  *references*, never secrets.
