# Configuration

All configuration is environment-based (see `.env.example`). Authoritative loader:
`src/n8n_cp/core/config.py`.

| Variable | Default | Meaning |
|----------|---------|---------|
| `N8N_BASE_URL` | — | Instance API base; should end with `/api/v1` (normalized). |
| `N8N_API_KEY` | — | API key (Settings → n8n API). Never logged/echoed/audited. |
| `N8N_REQUEST_TIMEOUT_MS` | 30000 | Per-request timeout. |
| `N8N_MAX_RETRIES` | 3 | Max retries for transient failures (4 attempts total). |
| `N8N_ALLOW_DESTRUCTIVE` | false | Must be true (plus a token) for destructive tools. |
| `N8N_ALLOW_PRODUCTION_WRITES` | false | Must be true (plus a token) for production-impact tools. |
| `N8N_DEFAULT_PROJECT_ID` | — | Optional default project for some operations. |
| `N8N_AUDIT_LOG_ENABLED` | true | Write JSONL audit records. |
| `N8N_REDACT_SECRETS` | true | Recursive secret redaction on all output. |
| `N8N_REDACT_EXECUTION_DATA` | true | Redact personal/secret data in execution payloads. |
| `N8N_BACKUP_DIR` | ./backups | Where workflow backups are written. |
| `N8N_AUDIT_DIR` | ./audit | Where audit JSONL files are written. |

## Safety switches
The two `ALLOW_*` flags are the master gates. With both false (the default), the
plane is effectively read-only + reversible-write only; activation, retries,
transfers, deletes and the like are blocked even if a token is supplied. This is
deliberate: an agent prompt cannot widen its own permissions — only the operator's
environment can.

## Confirmation tokens
Production/destructive tools, when first called, return a `confirmationToken`
bound to that exact operation + resource and valid for ~5 minutes. Re-call the
same tool with `--confirm <TOKEN>`. A token cannot authorize a different
operation or resource, and cannot be reused after it expires.

## Validate your setup
```bash
python3 -m n8n_cp doctor
```
Reports config problems (missing URL/key, suspicious timeout) without sending any
request. The API key is never included in this output.
