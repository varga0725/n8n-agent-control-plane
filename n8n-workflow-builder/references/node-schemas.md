# Node Schemas — getting parameters exactly right

The OpenAPI spec describes the **API**, not the **nodes**. But machine-readable
node schemas DO exist, and this skill can use them to validate parameters and
typeVersions. Three sources, from most to least convenient for offline use.

## 1. Pre-extracted JSON schemas (offline, no instance) — preferred
Project: `yigitkonur/n8n-schema-generator` (MIT). Auto-extracts a JSON schema for
every `n8n-nodes-base` node + credential and commits it to GitHub, updated hourly
as new n8n versions ship (~428 nodes, ~389 credentials). Readable directly from
GitHub raw — no auth, no running n8n.

Each node schema includes: `properties[]` (name, type, default, options,
displayOptions), `availableVersions`, `defaultVersion`, `defaults`, `inputs`,
`outputs`, `credentials`.

Use it with the bundled scripts:
```bash
# See a node's parameters + valid versions
python3 scripts/fetch_node_schema.py --type n8n-nodes-base.httpRequest --params-only

# Full schema JSON
python3 scripts/fetch_node_schema.py --type if

# Find nodes / list credentials' fields
python3 scripts/fetch_node_schema.py --search slack
python3 scripts/fetch_node_schema.py --credential postgres

# Cache schemas locally for offline + faster deep validation
python3 scripts/fetch_node_schema.py --type postgres --cache ./n8n-schemas
```

## 2. Deep workflow validation against those schemas
`validate_workflow.py --deep` now checks every node's `typeVersion` against the
node's `availableVersions` and flags unknown / missing top-level parameters — a
real parameter-level check, not just structure:
```bash
python3 scripts/validate_workflow.py my-workflow.json --deep
# offline / faster, using a local cache from fetch_node_schema.py --cache:
python3 scripts/validate_workflow.py my-workflow.json --deep --schema-dir ./n8n-schemas
```
It degrades gracefully: nodes with no available schema (LangChain/AI nodes,
community nodes, or when offline) are reported and skipped, never falsely failed.

## 3. The n8n-mcp connector (best for an agent) — recommended
Project: `czlonkowski/n8n-mcp` (MCP server). Ships a SQLite database of ~1,800+
nodes (core **and** community, incl. the LangChain/AI nodes the schema-generator
set omits) with ~99% property coverage, plus workflow/node **validation** tools.
Because it's an MCP, your agent can query node schemas and validate workflows as
first-class tools instead of shelling out.

Typical setup (stdio MCP, via npx):
```jsonc
// in your agent's MCP config
{
  "mcpServers": {
    "n8n-mcp": { "command": "npx", "args": ["-y", "n8n-mcp"] }
  }
}
```
It exposes tools to search nodes, fetch a node's full info/properties/docs/versions,
and validate a node config or a whole workflow. For the **control-plane** agent in
this repo's sibling project, adding n8n-mcp gives node-level intelligence to
complement the API-level control plane. (It can also connect to your live instance
for management, overlapping with the control plane — pick one for writes.)

## Which to use when
- Authoring offline / CI, base nodes → **fetch_node_schema.py** + `--deep`.
- You need AI/LangChain or community-node schemas, or want it as agent tools →
  **n8n-mcp**.
- You want the exact shape as configured on YOUR instance/version →
  **fetch_node_template.py** (reads your live instance).

## The other sources (for reference)
- **Canonical**: each node's `INodeTypeDescription` (`description.properties[]`)
  + its `.node.json` codex file, in the `n8n-nodes-base` source. Ground truth.
- **Instance internal API**: the editor loads all node descriptions from the
  running instance (`/types/nodes.json` / internal `/rest/node-types`). Available
  from a live instance but via the internal/browser-session API, not the public
  `/api/v1` key — so awkward for an API-key agent.
