# n8n Agent Control Plane

A safe, modular, auditable control plane over the **n8n Public REST API (v1.1.1)**
for AI agents (Claude Code, custom Python/TS agents, Hermes/OpenClaw) and CI/CD.

This is **not** a thin API wrapper. It operates on three levels:

1. **Primitive tools** — one fixed, named, risk-classified tool per API endpoint.
2. **Domain skills** — intelligent handling of workflows, executions, credentials,
   projects, users, data tables, organization, security and packages.
3. **High-level operations** — multi-step, validated, audited, recoverable flows
   (safe deploy, triage, recovery, backup/restore, bootstrap, health, security).

## Why it's safe by default

- **Read-only by default.** Production writes and destructive actions are blocked
  unless the operator sets `N8N_ALLOW_PRODUCTION_WRITES` / `N8N_ALLOW_DESTRUCTIVE`
  **and** a short-lived, operation-bound confirmation token is supplied.
- **Capability-first.** `GET /discover` decides what's even callable; beta/optional
  features stay off until confirmed.
- **Secrets never leak.** Recursive redaction on all output, audit and errors; the
  API key is never logged.
- **Everything write is audited.** Structured JSONL audit records (redacted).
- **No free-form HTTP tool.** Agents can only invoke named endpoints from the
  registry — there is no `method + path + body` escape hatch.

## Quick start

```bash
cp .env.example .env          # fill in N8N_BASE_URL and N8N_API_KEY
export PYTHONPATH=src         # runtime needs only the Python stdlib

python3 -m n8n_cp doctor       # validate config
python3 -m n8n_cp discover     # what does this instance support?
python3 -m n8n_cp tools        # list all primitive tools
python3 -m n8n_cp run n8n_workflow_list --param limit=5
python3 -m n8n_cp op instance_health_report
```

Destructive/production calls return an impact summary + a `confirmationToken`;
show it to the human, then re-run with `--confirm <TOKEN>`.

## Layout

```
src/n8n_cp/
  core/            config, auth, client, retry, rate_limit, redaction, audit,
                   risk, confirmation, pagination, idempotency, validation,
                   diff, backup, capabilities, capability_registry
  transports/      base (interface) + rest + cli + mock
  domains/         15 per-domain subpackages (typed wrappers over the registry)
  operations/      one file per high-level operation (13)
  generated/       typed Pydantic models generated from the OpenAPI spec
  endpoints.py     the registry: 80 fixed, risk-classified primitive tools
  tools.py         dispatcher (capability gate, pre-checks, safe execution)
skills/            11 agent skills (SKILL.md), one per domain + operations
policies/          permission / destructive / production / retry / redaction YAML
openapi/           n8n-openapi.json (Public API 1.1.1) + codegen notes
scripts/           generate_models.py (OpenAPI -> Pydantic)
tests/             unit + contract (incl. OpenAPI) + integration + smoke
docs/              INSTALLATION, CONFIGURATION, SECURITY, SKILLS, API_MAPPING, …
```

## Language note (Python, transport-agnostic)

The runtime is pure-stdlib Python so it runs with **no build step** anywhere an
agent or CI runner has Python. Strong typing is preserved by generating Pydantic
models from the OpenAPI spec (see `openapi/README.md`); generated code is never
hand-edited. The business logic talks to a `Transport` interface, so a TypeScript
or CLI transport can be added without touching the domains/operations.

See `docs/` for full documentation and `docs/API_MAPPING.md` for the complete
endpoint → tool → skill → risk table (80 tools).
