---
name: n8n-credentials
description: >
  Manage n8n credentials safely: list metadata, fetch a credential type's schema,
  create, update, test, transfer between projects, and delete — always with
  secret redaction. Use this skill WHENEVER the user works with credentials,
  connections, API keys/tokens stored in n8n, or asks "which credential does this
  workflow use", "test the Slack credential", "rotate this token", "delete unused
  credentials". Credential secrets must NEVER appear in output, logs, or audit
  records. Before deleting a credential, find the workflows that use it.
version: 1.0.0
risk_level: mixed
---

# n8n Credentials

Credentials hold secrets. The overriding rule: secrets are referenced, tested and
managed — never echoed. Every response, log line and audit entry is redacted.

## When to use
- Listing credential metadata; reading a credential type's required fields.
- Creating/updating a credential; testing whether it authenticates.
- Transferring a credential to another project; deleting an unused one.
- Validating credentials at scale → operation `credential_validation`.

## When NOT to use
- Embedding secrets into workflow JSON (you can't, and shouldn't) — workflows
  reference credentials by id/name.

## Tools
Read: `n8n_credential_list`, `n8n_credential_get`, `n8n_credential_get_schema`,
`n8n_credential_test` (result redacted).
Reversible: `n8n_credential_create`, `n8n_credential_update`.
Production-impact: `n8n_credential_transfer`.
Destructive: `n8n_credential_delete`.
Operation: `credential_validation`.

## Inputs
- `n8n_credential_get_schema` needs `credentialTypeName` (e.g. `slackApi`,
  `httpHeaderAuth`); call it first to learn what `data` fields a create requires.
- `n8n_credential_create` body: `name`, `type`, `data` (the secret fields).

## Secret handling (non-negotiable)
- Never print, log, or store API keys, tokens, passwords, private keys, secrets.
- Never write raw credential payloads to debug logs.
- The credential `test` result is also redacted before it is returned.
- Note: some instances do not expose a credential **list** endpoint; if so, work
  from explicit IDs.

## Pre-checks
- Delete → find workflows that reference the credential first (a broken
  credential reference silently breaks those flows). Use `credential_validation`.
- Transfer → validate the destination project exists and is intended.

## Confirmation rules
Transfer (production-impact) and delete (destructive) require the env flag and an
operation-bound confirmation token.

## Forbidden
- Returning or logging any secret value.
- Deleting a credential still in use without surfacing the dependent workflows.

## Examples
- "Does the Slack credential still work?" →
  `credential_validation --json '{"id":"42"}'` → reports pass/fail, redacted.
- "What fields do I need for a Postgres credential?" →
  `n8n_credential_get_schema --param credentialTypeName=postgres`.
- "Delete credential 42" → `credential_validation` to find dependents → confirm →
  `n8n_credential_delete` with token.
