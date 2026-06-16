---
name: n8n-workflow-builder
description: >-
  Build, validate, and deploy n8n automation workflows end-to-end via the n8n
  public REST API. Use this skill WHENEVER the user wants to create, design,
  generate, edit, fix, or deploy an n8n workflow or automation — even if they
  only describe the automation ("when a Telegram message arrives, save it to
  Google Sheets", "every morning fetch RSS and post to Slack", "an AI agent that
  answers emails") without naming n8n explicitly, as long as n8n is the target
  platform. Also use it for questions about n8n workflow JSON structure, node
  types, connections, expressions, flow logic (IF/Switch/Merge/Loop/error
  handling), credentials, or the n8n API. This skill produces valid, importable
  workflow JSON and can push it straight to a live n8n instance.
---

# n8n Workflow Builder

This skill lets you produce **valid, importable, deployable** n8n workflows. The
core deliverable is always a workflow JSON object that conforms to n8n's schema,
which you can either hand to the user for manual import or push directly to their
n8n instance through the public REST API.

n8n changes fast, and node `typeVersion`s and parameters drift between releases.
When you are unsure about a specific node's current parameters or version, **look
it up** rather than guessing — see "Staying current" below. A workflow that
imports cleanly but uses a stale parameter shape will silently misbehave, which
is worse than asking.

## Workflow at a glance

1. **Clarify the automation.** What triggers it? What are the steps? Which apps
   and credentials are involved? What should happen on error? Don't over-ask —
   infer sensible defaults and state them.
2. **Pick the trigger + nodes.** Map each step to a node type. See
   `references/core-nodes.md`, `references/ai-nodes.md`, and the live node
   catalog (https://docs.n8n.io/integrations/builtin/node-types/).
3. **Build the JSON.** Assemble `nodes` + `connections` + `settings`. The schema
   and every rule that bites in practice are in `references/workflow-schema.md`.
   Read it before building your first workflow — the connection format and
   expression syntax are the two things most often gotten wrong.
4. **Validate.** Run `scripts/validate_workflow.py <file.json>` to catch
   structural errors (orphan connections, duplicate node names, bad positions,
   missing required fields) before anything touches the live instance.
5. **Deploy (if requested).** Use `scripts/n8n_api.py` to create/update/activate
   on the user's instance. API details are in `references/api.md`.
6. **Confirm.** Report the workflow ID and URL, and tell the user what
   credentials they still need to wire up in the n8n UI.

## The two things that break most workflows

**Connections are keyed by node *name*, not ID, and the value is an array of
arrays.** Each output port is an outer array element; parallel branches from one
port are inner array elements. Get this wrong and the workflow imports but the
nodes aren't actually wired. Full explanation with examples in
`references/workflow-schema.md`.

**Credentials are referenced, never embedded.** A node points at a credential
that must already exist in the target instance (by `id` + `name`). You cannot
create a working credential's secret through the workflow JSON. Always tell the
user which credentials they need to create/select after import. The public API
can create credentials (`POST /credentials`) but cannot list existing ones, so
when deploying, ask the user for credential IDs or have them wire credentials in
the UI after the push.

## Building the JSON — minimum viable shape

```json
{
  "name": "My Workflow",
  "nodes": [
    {
      "parameters": {},
      "id": "a1b2c3d4-0001-0000-0000-000000000001",
      "name": "When clicking 'Execute workflow'",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [0, 0]
    },
    {
      "parameters": { "url": "https://api.example.com/data", "options": {} },
      "id": "a1b2c3d4-0002-0000-0000-000000000002",
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [220, 0]
    }
  ],
  "connections": {
    "When clicking 'Execute workflow'": {
      "main": [[{ "node": "HTTP Request", "type": "main", "index": 0 }]]
    }
  },
  "settings": { "executionOrder": "v1" }
}
```

Rules that matter (the full set is in `references/workflow-schema.md`):

- `name`, `nodes`, `connections`, `settings` are **required**. `active`, `id`,
  `tags`, `createdAt`, `updatedAt` are **read-only** — never send them in a
  create/update body; activate separately via the API.
- Every node needs a unique `name` and a unique `id` (UUID). `position` is
  `[x, y]`; space nodes ~220px apart on x so the canvas is readable.
- Always include `"executionOrder": "v1"` in `settings` for current behavior.
- Set `typeVersion` to the node's current major — when unsure, look it up; an
  outdated version can change how parameters are interpreted.
- Expressions use `={{ ... }}`. A string is an expression only if it starts with
  `=`. Reference upstream data with `{{ $json.field }}` or
  `{{ $('Node Name').item.json.field }}`.

## Reference files — read the relevant one before building

- `references/workflow-schema.md` — **Read this first.** The complete JSON
  schema, the connection format in depth, node anatomy, expressions, pinData,
  and the validation rules the script enforces.
- `references/api.md` — Public REST API: auth, base URL, every workflow /
  execution / credential / tag endpoint, pagination, and exact curl + script
  examples for create → activate → verify.
- `references/core-nodes.md` — The everyday nodes (triggers, HTTP, Code, Set,
  IF, Switch, Merge, Filter, Loop, Wait, schedule, webhook) with their current
  `type`, `typeVersion`, and parameter shapes.
- `references/ai-nodes.md` — LangChain/AI nodes (AI Agent, chat models, memory,
  tools, vector stores) and the all-important `ai_*` connection types, which
  work differently from `main` connections.
- `references/flow-logic.md` — Patterns for branching, merging, looping over
  items, waiting, sub-workflows, and error handling.
- `references/complex-patterns.md` — **For non-trivial workflows.** Complete,
  validated, copy-paste example workflows in `references/examples/` (branching +
  batched loop + error handling, API pagination loop, global error workflow, RAG
  AI agent) with the wiring decisions explained. Start from these skeletons.
- `references/data-and-expressions.md` — The item data model, item linking /
  paired items, Split Out vs. Aggregate, Luxon dates, JMESPath, referencing
  multiple upstream nodes. Read this whenever a workflow loops, merges, or
  reshapes data across branches.
- `references/node-schemas.md` — **Getting node parameters exactly right.**
  Machine-readable node schemas exist: pull a node's exact parameters/versions
  offline with `scripts/fetch_node_schema.py`, validate a workflow's params with
  `validate_workflow.py --deep`, or use the `n8n-mcp` connector for full
  (incl. AI/community) node schemas as agent tools. Read this when a node's
  parameter shape or typeVersion is uncertain.

## Scripts

- `scripts/validate_workflow.py <workflow.json>` — Structural validation. Run it
  on every workflow before deploy. Exits non-zero and prints specific problems
  if the JSON won't behave. Add `--deep` to also validate each node's typeVersion
  and parameters against real node schemas (see `references/node-schemas.md`).
- `scripts/fetch_node_schema.py` — Fetch a node's exact parameter schema offline
  (no live instance) from the auto-updated community schema set; also powers
  `--deep`. E.g. `python3 scripts/fetch_node_schema.py --type
  n8n-nodes-base.httpRequest --params-only`.
- `scripts/n8n_schemas.py` — shared schema loader used by the two above.
- `scripts/n8n_api.py` — Thin CLI over the public API. Subcommands: `list`,
  `get`, `create`, `update`, `activate`, `deactivate`, `delete`, `executions`.
  Reads `N8N_BASE_URL` and `N8N_API_KEY` from the environment. See
  `references/api.md` for usage.
- `scripts/fetch_node_template.py` — Pull the EXACT current JSON of a node type
  (or a whole workflow) from a live instance to use as a template. This is the
  reliable way to nail version-specific node `parameters`/`typeVersion` that
  aren't in any spec. E.g. `python3 scripts/fetch_node_template.py --type
  n8n-nodes-base.postgres`.

## Staying current

Node parameters, `typeVersion`s, and even node names change between n8n releases.
When you need to confirm the current shape of a specific node or API endpoint,
consult these in order of authority:

1. The user's own instance API docs (Swagger): their n8n base URL + `/api/v1/docs`.
2. The node catalog: https://docs.n8n.io/integrations/builtin/node-types/ — each
   node page documents its operations and parameters.
3. The API reference: https://docs.n8n.io/api/ and the OpenAPI spec the docs
   render. Flow-logic concepts: https://docs.n8n.io/flow-logic/.

A reliable trick when you have API access: build a similar workflow once in the
n8n UI, then `GET` it through the API to see the exact current JSON for those
nodes, and use that as your template. Reading a real export beats guessing.

## After delivering

When you deploy or hand off a workflow, tell the user plainly: the workflow ID
and URL, which credentials they must create or select in the UI, and whether you
left it active or inactive. If anything depended on a guessed parameter or
version, flag it so they can verify in the editor.
