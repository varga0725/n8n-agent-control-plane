# Testing

Four layers, mirroring the spec.

## Unit (offline)
`tests/unit/` — pure functions, no network:
- secret redaction (recursive, allowlist)
- retry decisions + backoff schedule
- risk classification & gating
- confirmation token issue/verify (expiry, binding, replay)
- pagination clamping & collection
- error normalization / envelope shape
- workflow diff
- backup round-trip & read-only stripping

```bash
export PYTHONPATH=src
python3 -m pytest tests/unit -q
```

## Contract (offline, mock transport + policy)
`tests/contract/` — uses `MockTransport`:
- every registry tool has a valid method/path/risk and required path params
- `policies/permissions.yaml` risk levels match `endpoints.py` (no drift)
- request bodies for write tools are well-formed
- confirmation flow end-to-end (blocked → token → proceed)

```bash
python3 -m pytest tests/contract -q
```

## Integration (against a disposable n8n)
`tests/integration/` — requires `N8N_BASE_URL` + `N8N_API_KEY` to a **test**
instance. Exercises create/get/update/activate/deactivate/archive/unarchive/
delete for workflows; execution list/get; credential schema/test; project
create/update/delete; data table create + row insert/update/upsert/delete +
table delete. Gated behind an env flag so it never runs by accident:

```bash
N8N_RUN_INTEGRATION=1 N8N_ALLOW_DESTRUCTIVE=1 N8N_ALLOW_PRODUCTION_WRITES=1 \
  python3 -m pytest tests/integration -q
```

## Production smoke (read-only only)
`tests/smoke/` — safe to run against production; only:
discover, workflow list (limit 1), execution list (limit 1), project list
(limit 1), credential list (limit 1), insights summary.

```bash
N8N_RUN_SMOKE=1 python3 -m pytest tests/smoke -q
```

Fixtures live in `tests/fixtures/` (sample workflow JSON, discover payloads,
execution responses).
