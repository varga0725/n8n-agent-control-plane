# Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `doctor` says API key not set | `N8N_API_KEY` missing | Set it in the environment / `.env`. |
| `401 auth_error` | bad/expired API key | Regenerate in Settings → n8n API. |
| `403 permission_error` | key scope or role too low | Use a key with sufficient scope. |
| `capability_unavailable` | feature off / older n8n | Run `discover`; enable the feature, or it's not in this edition. |
| `beta_disabled` (n8n-packages) | beta flag off | Set `N8N_PUBLIC_API_PACKAGES_ENABLED=true` on the server; confirm via `discover`. |
| `policy_blocked` on a write | safety flag off | Set `N8N_ALLOW_PRODUCTION_WRITES` / `N8N_ALLOW_DESTRUCTIVE` (intentionally). |
| `confirmation_required` | needs approval | Show the impact to the user; re-run with `--confirm <TOKEN>`. |
| `confirmation_error: expired` | token older than ~5 min | Re-run the preview to mint a fresh token. |
| `retry_unsafe` on execution retry | non-idempotent side effects | Inspect the run; retry manually only if truly safe. |
| `validation_error` empty filter | data-table delete/update w/o filter | Provide an explicit, specific filter. |
| Network timeouts retried then fail | instance unreachable (e.g. Tailscale down) | Check connectivity to `N8N_BASE_URL`. |
| Empty body from instance | wrong base URL (missing `/api/v1`) | Fix `N8N_BASE_URL`; `doctor` warns about this. |

## Debugging tips
- Add `--dry-run` to any `run`/`op` to see exactly what would be called, with the
  impact summary, without sending the request.
- Inspect `./audit/audit-YYYY-MM-DD.jsonl` for a redacted trace of every action.
- `python3 -m n8n_cp tools --domain <domain>` shows the exact tool names + paths.
- Never work around restrictions by hand-crafting HTTP calls — there is no
  free-form HTTP tool on purpose.
