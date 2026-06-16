# Flow Logic Patterns

How to wire the common control-flow shapes correctly. The recurring trap is the
connection nesting (array of ports, each an array of targets) — see
`workflow-schema.md` if any of this looks unfamiliar.

## Branching with IF (two outputs)

`IF` has two output ports: `main[0]` = true, `main[1]` = false.

```json
"IF": { "main": [
  [ { "node": "Handle True",  "type": "main", "index": 0 } ],
  [ { "node": "Handle False", "type": "main", "index": 0 } ]
] }
```

## Multi-way with Switch (one port per rule)

`Switch` emits one output port per rule, in rule order. Wire each port to its
branch:

```json
"Switch": { "main": [
  [ { "node": "Route A", "type": "main", "index": 0 } ],
  [ { "node": "Route B", "type": "main", "index": 0 } ],
  [ { "node": "Fallback", "type": "main", "index": 0 } ]
] }
```

## Merging branches back together

A `Merge` node has multiple **inputs**. Two upstream branches both point at the
Merge node but at different input indexes:

```json
"Branch A": { "main": [[ { "node": "Merge", "type": "main", "index": 0 } ]] },
"Branch B": { "main": [[ { "node": "Merge", "type": "main", "index": 1 } ]] }
```

`index: 0` = first input, `index: 1` = second. Modes: `append` stacks items,
`combine` joins by position or matching field, `chooseBranch` passes one branch.

## Fan-out: one node feeding several in parallel

Single output port, multiple targets in the same inner array:

```json
"Source": { "main": [[
  { "node": "Task 1", "type": "main", "index": 0 },
  { "node": "Task 2", "type": "main", "index": 0 },
  { "node": "Task 3", "type": "main", "index": 0 }
]] }
```

## Looping over items in batches

Most nodes already process every item, so you rarely need an explicit loop. Use
**Loop Over Items** (`splitInBatches`) when you must process in chunks (rate
limits, pagination, per-item API calls). It has two outputs: `main[0]` = "done"
(after all batches), `main[1]` = "loop" (the current batch). Wire the loop body's
end **back into** the Loop node:

```json
"Loop Over Items": { "main": [
  [ { "node": "Finish", "type": "main", "index": 0 } ],
  [ { "node": "Process Batch", "type": "main", "index": 0 } ]
] },
"Process Batch": { "main": [[ { "node": "Loop Over Items", "type": "main", "index": 0 } ]] }
```

The body (`Process Batch`) loops back to the Loop node; when batches are
exhausted, execution continues from the "done" output.

## Waiting / delaying

Use the **Wait** node to pause (fixed interval, until a timestamp, or until a
webhook/resume URL is hit). For polling, combine Wait inside a batch loop. For
scheduled starts, use the Schedule Trigger instead of waiting.

## Sub-workflows

Call another workflow with **Execute Sub-workflow**
(`n8n-nodes-base.executeWorkflow`); the callee starts with an **Execute
Sub-workflow Trigger** (`n8n-nodes-base.executeWorkflowTrigger`). Good for reuse
and for exposing a workflow as an AI agent tool (`toolWorkflow`). Pass data in
via the trigger's input and return the callee's last-node output.

## Error handling

Three complementary mechanisms:

1. **Per-node `continueOnFail`** — set `"onError": "continueRegularOutput"` (or
   `"continueErrorOutput"` to route failures to a second output) in the node so a
   single bad item doesn't abort the run. Older nodes use
   `"continueOnFail": true`.
2. **Stop and Error node** (`n8n-nodes-base.stopAndError`) — deliberately fail
   with a custom message when a business rule is violated.
3. **Error Workflow** — set `settings.errorWorkflow` to the ID of a workflow
   whose trigger is the **Error Trigger** (`n8n-nodes-base.errorTrigger`). It
   runs automatically when this workflow errors, receiving the error details —
   the standard way to send failure alerts to Slack/email.

A robust production workflow usually pairs `onError` on risky nodes (HTTP calls,
DB writes) with a dedicated error workflow for notification.

## Execution order

With `settings.executionOrder: "v1"`, multi-branch workflows run in a
predictable order (top-to-bottom by node position, branch by branch). Always set
it. If branches must rejoin before a step proceeds, route them through a Merge
node rather than relying on timing.
