---
name: n8n-discovery
description: >
  Discover which features an n8n instance supports BEFORE doing anything else.
  Use this skill at the start of any n8n control-plane session, whenever you are
  unsure whether a feature (data tables, projects, insights, source control,
  community/n8n packages, audit) is available, or when a tool returns
  "capability_unavailable". It calls GET /discover and builds the capability
  registry the other n8n skills rely on. Always run discovery first.
version: 1.0.0
risk_level: read_only
---

# n8n Discovery

Capability-first operation is the foundation of this control plane: never call a
feature the instance doesn't expose, hasn't enabled, or that the API key's scope
forbids. This skill answers "what can I safely do here?".

## When to use
- At the start of every session, before workflow/execution/etc. work.
- When any tool returns `capability_unavailable` or `beta_disabled`.
- When deciding whether an optional domain (data-tables, projects, insights,
  source-control, packages) is usable.

## When NOT to use
- For the actual work — once you know the capabilities, use the domain skills.

## Tool
- `n8n_discover_capabilities` → `GET /discover` (read-only).

Run it:
```bash
python3 -m n8n_cp discover
```

## Expected output
The standard envelope. `data` contains the raw `/discover` payload; the client
also derives an internal capability set. Treat a domain as usable only if it is
in the available set and not in the disabled set.

## Behavior on older instances
If `/discover` is absent (older n8n), only the baseline domains (workflows,
executions, credentials, tags) are assumed available; optional/beta features are
treated as unavailable until proven otherwise. You can override per-call with
`force=true`, but only do so when you are certain the feature exists.

## Rules
- Do not call optional/beta endpoints without confirming availability here first.
- Beta features (e.g. n8n-packages) stay disabled unless discovery shows them on.
