# Changelog

## 1.1.0 — full spec compliance pass
- **OpenAPI spec integrated** (`openapi/n8n-openapi.json`, n8n Public API 1.1.1).
  Registry verified 1:1 against it: 80/80 endpoints, zero missing, zero extra.
- **Typed models generated** (`src/n8n_cp/generated/models/`, 121 Pydantic v2
  classes) via `scripts/generate_models.py` / `make models`. Runtime stays
  stdlib-only; the typed models are an opt-in layer.
- **OpenAPI contract tests** (`tests/contract/test_openapi_contract.py`) —
  validate every tool's method/path/params against the real spec.
- **Literal file structure** matching the specification's tree:
  - `domains/` — 15 per-domain subpackages with typed wrappers over the registry.
  - `operations/` — one file per operation (13 incl. `workflow_migration`).
  - `core/` — added `auth.py`, `rate_limit.py`, `capability_registry.py`
    (+ `audit_log.py` / `risk_classifier.py` spec-name aliases).
  - `transports/` — added `cli.py` (`N8nCliTransport`).
- `Makefile` for install/models/test/doctor/tools.

## 1.0.0 — initial release
- Core infrastructure: config, REST/mock transports, safe client, retry with
  backoff+jitter, error normalization, recursive secret redaction, structured
  audit logging, four-level risk classification, operation-bound confirmation
  tokens, pagination guards, idempotency heuristics, workflow diff, backup/restore.
- Endpoint registry: 80 fixed, named, risk-classified primitive tools covering
  the n8n Public API v1.1.1. No free-form HTTP tool.
- 12 high-level operations + 11 domain skills (SKILL.md) + policies.
- CLI: `doctor`, `discover`, `tools`, `run`, `op`.
- Docs: README, INSTALLATION, CONFIGURATION, SECURITY, SKILLS, API_MAPPING,
  TESTING, TROUBLESHOOTING.
- Tests: unit + contract (mock transport); integration + smoke scaffolding.

### Known limitations / next steps
- Integration tests require a disposable n8n instance and are env-gated.
- `/discover` payload parsing is defensive across versions; tighten once the
  exact runtime shape from the target instance is captured.
