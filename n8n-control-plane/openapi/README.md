# OpenAPI spec & typed model generation

The endpoint registry (`src/n8n_cp/endpoints.py`) is the authoritative list of
callable tools. This directory is for the instance's **OpenAPI 3.0 spec**, which
drives optional typed-model generation and contract tests.

## 1. Get the spec from your instance
The Swagger UI is at `<N8N_BASE_URL>/api/v1/docs`. The raw spec is typically one
of:
- `<N8N_BASE_URL>/api/v1/docs/swagger.json`
- `<N8N_BASE_URL>/api/v1/openapi.yml`

Save it here as `n8n-openapi.json` (or `.yml`). (For the target instance this is
behind Tailscale, so fetch it from a machine on the tailnet and copy it in.)

## 2. Generate typed models (never hand-edit the output)
Python (Pydantic v2) via `datamodel-code-generator`:

```bash
pip install datamodel-code-generator
datamodel-codegen \
  --input openapi/n8n-openapi.json \
  --input-file-type openapi \
  --output src/n8n_cp/generated/models.py \
  --target-python-version 3.10
```

`src/n8n_cp/generated/` is generated code: do not edit by hand; regenerate when
the API version changes. The hand-written safety/business logic sits *above* it.

## 3. Contract tests
`tests/contract/` can load this spec to assert that every registry tool's
method/path exists in the spec and that request/response shapes line up. This is
how you catch drift when n8n bumps the API version — regenerate models, re-run
contract tests, fix any registry rows that changed.

## TypeScript transport (optional)
The architecture is transport-agnostic. To add a TS client, generate types with
`openapi-typescript` from the same spec and implement the `Transport` interface
in a Node sidecar; the Python domains/operations stay unchanged.
