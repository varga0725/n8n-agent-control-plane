# n8n Agent Control Plane

**Safe, auditable n8n automation for AI agents.** Two complementary, MIT-licensed
skill packages that let an agent (Claude Code, OpenClaw, custom Python/TS agents,
CI/CD) build *and* operate [n8n](https://n8n.io) — without the usual risk of an
LLM silently breaking production.

| Package | What it does |
|---------|--------------|
| [`n8n-control-plane/`](./n8n-control-plane) | **Operate** an n8n instance via the Public API: 80 risk-classified primitive tools + 13 high-level operations + 11 domain skills. Read-only by default; destructive/production actions require an env flag **and** a short-lived confirmation token; every write is audited and secrets are redacted. |
| [`n8n-workflow-builder/`](./n8n-workflow-builder) | **Author** valid, importable workflow JSON from a description — schema, node references, flow-logic, validated complex examples, and offline node-schema validation. |

The two fit together: build a workflow with `n8n-workflow-builder`, then deploy
and manage it safely with `n8n-control-plane`.

## Why "safe ops"
Most n8n + AI tooling focuses on *building* workflows. This project's differentiator
is **governance**: risk classification (read-only / reversible / production-impact /
destructive), operation-bound confirmation tokens, mandatory backup + diff before
editing an active workflow, idempotency-guarded execution retries (never auto-retry
payments/emails), capability discovery (`/discover`) before acting, recursive secret
redaction, and structured audit logging. There is no free-form `method + path + body`
tool — an agent can only call fixed, named, risk-tagged endpoints.

## Quick start (for agents & humans)
```bash
# Control plane
cd n8n-control-plane
pip install -e .                       # gives the `n8n-cp` command (avoids python/python3 issues)
export N8N_BASE_URL="https://your-n8n/api/v1"
export N8N_API_KEY="..."               # Settings -> n8n API
n8n-cp doctor                          # validate config (no calls)
n8n-cp discover                        # what does this instance support?
n8n-cp tools                           # list all 80 primitive tools
n8n-cp op instance_health_report
```

If you can't `pip install`, run from source with `PYTHONPATH=src python3 -m n8n_cp ...`
(use `python3`, not `python` — many systems lack the `python` alias).

## Verify it
```bash
cd n8n-control-plane && PYTHONPATH=src python3 -m pytest -q       # 32 offline tests
bash n8n-control-plane/scripts/run_local_n8n_test.sh             # real end-to-end vs a throwaway Docker n8n
```

## Status & safety
Verified against the official **n8n Public API 1.1.1** OpenAPI spec (80/80 endpoints).
Offline unit + contract + OpenAPI-contract tests pass. Integration/smoke tests are
env-gated and run against a disposable instance (see each package's `docs/TESTING.md`).
Because the control plane can perform destructive operations, test against a
**disposable** instance first and keep the `N8N_ALLOW_*` flags off in production
unless you mean it.

## Credits
Node-schema tooling references the MIT-licensed
[yigitkonur/n8n-schema-generator](https://github.com/yigitkonur/n8n-schema-generator)
and recommends [czlonkowski/n8n-mcp](https://github.com/czlonkowski/n8n-mcp) for
node-level schemas as agent tools. n8n is a trademark of n8n GmbH; this is an
independent, unaffiliated project.

## License
MIT — see [LICENSE](./LICENSE).
