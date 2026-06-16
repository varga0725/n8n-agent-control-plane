# n8n Workflow JSON Schema

This is the contract every workflow must satisfy to import cleanly and run. The
public API validates `name`, `nodes`, `connections`, and `settings`; everything
else here is what makes the workflow actually *work* once imported.

## Top-level object

```json
{
  "name": "string (required)",
  "nodes": [ /* array of Node objects, required */ ],
  "connections": { /* object, required */ },
  "settings": { /* object, required — {} is valid but prefer executionOrder */ },
  "pinData": { /* optional, test data pinned to nodes */ },
  "staticData": null
}
```

Read-only fields the API rejects on create/update: `id`, `active`, `createdAt`,
`updatedAt`, `tags`. Do not include them in a create/update body. Activation and
tagging are separate API calls (see `api.md`).

## Node object

```json
{
  "parameters": { },
  "id": "uuid-v4 string, unique within the workflow",
  "name": "Human Readable Name, unique within the workflow",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "position": [x, y],
  "credentials": { },
  "notes": "optional string",
  "disabled": false
}
```

| Field | Notes |
|-------|-------|
| `parameters` | Node-specific config. Empty `{}` is valid for some triggers. The shape depends entirely on the node + `typeVersion` — see the per-node references and the live node docs. |
| `id` | UUID v4. Must be unique. n8n generates these; you can too. |
| `name` | Must be unique — **connections reference nodes by this name**, so a duplicate name silently breaks wiring. |
| `type` | Fully-qualified: `n8n-nodes-base.<node>` for core/integrations, `@n8n/n8n-nodes-langchain.<node>` for AI nodes. Case-sensitive. |
| `typeVersion` | Number (can be a float like `4.2`). Picks the parameter schema. Use the current major; an outdated value reinterprets parameters. |
| `position` | `[x, y]` pixel coords on the canvas. Lay left→right, ~220px apart on x; offset y for parallel branches. Purely visual but keep it tidy. |
| `credentials` | See below. Omit if the node needs none. |

### Credentials on a node

Current n8n uses an object with `id` and `name`:

```json
"credentials": {
  "telegramApi": { "id": "7", "name": "My Telegram Bot" }
}
```

Older exports use just the name string (`"telegramApi": "My Telegram Bot"`).
Prefer the object form. The key (`telegramApi`, `httpHeaderAuth`, `openAiApi`,
…) is the **credential type name**, which is specific to the node. The
referenced credential must already exist in the target instance — the workflow
JSON references it, it does not create it. After import, the user selects or
creates the actual credential in the editor.

## Connections — the part most often gotten wrong

`connections` is an object keyed by the **source node's name**. The value maps an
output type (`main`, or an `ai_*` type) to an **array of output ports**, where
each port is an **array of connection targets**.

```json
"connections": {
  "Source Node Name": {
    "main": [
      [ { "node": "Target A", "type": "main", "index": 0 } ],
      [ { "node": "Target B", "type": "main", "index": 0 } ]
    ]
  }
}
```

Decode the nesting:

- **Outer array** = output ports of the source node, in order. A normal node has
  one port (`main[0]`). An `IF` node has two (`main[0]` = true, `main[1]` =
  false). A `Switch` has one per rule.
- **Inner array** = all targets fed by that one port. Two entries means the port
  fans out to two nodes in parallel.
- Each **target object**: `node` (target's name), `type` (almost always
  `"main"`), `index` (which *input* of the target, usually `0`).

Examples:

Linear A → B:
```json
"A": { "main": [[ { "node": "B", "type": "main", "index": 0 } ]] }
```

One node fanning out to B and C in parallel (single port, two targets):
```json
"A": { "main": [[
  { "node": "B", "type": "main", "index": 0 },
  { "node": "C", "type": "main", "index": 0 }
]] }
```

IF node routing true→B, false→C (two ports, one target each):
```json
"IF": { "main": [
  [ { "node": "B", "type": "main", "index": 0 } ],
  [ { "node": "C", "type": "main", "index": 0 } ]
] }
```

A port with no targets is `[]` (empty inner array); keep it as a placeholder if
later ports are used.

## Expressions

Any parameter value can be a static value or an **expression**. A string is
treated as an expression only when it **starts with `=`**:

```json
"text": "=Hello {{ $json.firstName }}, you have {{ $json.count }} messages"
"url":  "=https://api.example.com/users/{{ $json.userId }}"
"value": "={{ $json.price * 1.27 }}"
```

Common expression references:

- `{{ $json.field }}` — a field from the current item's JSON.
- `{{ $json["field with spaces"] }}` — bracket form for awkward keys.
- `{{ $('Node Name').item.json.field }}` — a field from a specific upstream node.
- `{{ $('Node Name').all() }}` — all items from a node.
- `{{ $now }}`, `{{ $today }}` — Luxon date helpers.
- `{{ $input.item.json }}`, `{{ $itemIndex }}`, `{{ $runIndex }}`, `{{ $vars.* }}`.

Inside the Code node you instead use JS/Python directly (`$input.all()`,
`items`, `$json`) — that's code, not the `={{ }}` expression syntax.

## pinData (optional)

Pins sample output to a node so downstream nodes can be built/tested without
re-running upstream. Keyed by node name, value is an array of items:

```json
"pinData": {
  "HTTP Request": [ { "json": { "id": 1, "title": "example" } } ]
}
```

Useful when handing the user a workflow they can run immediately without live
credentials. Optional; omit if not needed.

## settings

```json
"settings": {
  "executionOrder": "v1",
  "saveManualExecutions": true,
  "saveExecutionProgress": true,
  "saveDataErrorExecution": "all",
  "saveDataSuccessExecution": "all",
  "timezone": "Europe/Budapest",
  "errorWorkflow": "<workflow-id of an error handler>"
}
```

`{}` is accepted, but always include at least `"executionOrder": "v1"` so
multi-branch execution order matches current n8n behavior.

## Validation checklist (what `validate_workflow.py` enforces)

- Required top-level keys present (`name`, `nodes`, `connections`, `settings`).
- Each node has `name`, `type`, `typeVersion`, `position`; node `name`s and
  `id`s are unique.
- Every connection source name and every target `node` exists in `nodes`.
- `position` is a 2-number array; `connections` nesting is array-of-arrays.
- At least one trigger node (type ending in `Trigger`, or `manualTrigger`,
  `webhook`, `cron`, `scheduleTrigger`) unless it's an explicit sub-workflow.
- Warns on read-only fields included in the body, and on nodes with no
  incoming/outgoing connections (likely orphan).
