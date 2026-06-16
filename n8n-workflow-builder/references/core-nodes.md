# Core & Common Integration Nodes

Current `type`, typical `typeVersion`, and the parameter shapes you actually
need. `typeVersion`s move over time — when a node misbehaves on the target
instance, confirm against its docs page
(`https://docs.n8n.io/integrations/builtin/core-nodes/<type>/`) or fetch a real
export from the instance. Treat the versions here as sensible current defaults,
not gospel.

## Triggers (a workflow needs exactly one entry point)

**Manual Trigger** — run on demand from the editor.
```json
{ "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1,
  "name": "When clicking 'Execute workflow'", "parameters": {} }
```

**Schedule Trigger** — time-based (replaces the old Cron node).
```json
{ "type": "n8n-nodes-base.scheduleTrigger", "typeVersion": 1.2,
  "name": "Schedule Trigger",
  "parameters": { "rule": { "interval": [ { "field": "hours", "hoursInterval": 1 } ] } } }
```
For a fixed time daily: `{ "field": "days", "triggerAtHour": 9 }`. For cron
expressions: `{ "field": "cronExpression", "expression": "0 9 * * 1-5" }`.

**Webhook** — HTTP entry point; the workflow's external trigger.
```json
{ "type": "n8n-nodes-base.webhook", "typeVersion": 2,
  "name": "Webhook",
  "parameters": { "httpMethod": "POST", "path": "my-hook", "responseMode": "onReceived" } }
```
`responseMode: "lastNode"` returns the final node's output; pair with a
**Respond to Webhook** node for custom responses.

**App triggers** — e.g. `n8n-nodes-base.telegramTrigger`,
`n8n-nodes-base.gmailTrigger`, `n8n-nodes-base.slackTrigger`. These need
credentials and usually an event/resource parameter.

## HTTP Request — the universal connector

```json
{ "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "name": "HTTP Request",
  "parameters": {
    "method": "POST",
    "url": "https://api.example.com/v1/items",
    "sendHeaders": true,
    "headerParameters": { "parameters": [ { "name": "Accept", "value": "application/json" } ] },
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify({ title: $json.title }) }}",
    "options": {}
  } }
```
For auth via a stored credential, set `"authentication": "predefinedCredentialType"`
or `"genericCredentialType"` and attach `credentials`. Keep `"options": {}` even
when empty.

## Code — arbitrary JS/Python

```json
{ "type": "n8n-nodes-base.code", "typeVersion": 2, "name": "Code",
  "parameters": {
    "mode": "runOnceForAllItems",
    "language": "javaScript",
    "jsCode": "return items.map(i => ({ json: { ...i.json, doubled: i.json.value * 2 } }));"
  } }
```
`mode` is `runOnceForAllItems` (see all items via `items`/`$input.all()`) or
`runOnceForEachItem` (use `$json` for the single item). For Python set
`"language": "python"` and use `pythonCode`.

## Set / Edit Fields — shape the data

```json
{ "type": "n8n-nodes-base.set", "typeVersion": 3.4, "name": "Edit Fields",
  "parameters": {
    "mode": "manual",
    "assignments": { "assignments": [
      { "id": "1", "name": "fullName", "type": "string",
        "value": "={{ $json.first }} {{ $json.last }}" }
    ] },
    "options": {}
  } }
```

## IF — boolean branch (two outputs: true=main[0], false=main[1])

```json
{ "type": "n8n-nodes-base.if", "typeVersion": 2, "name": "IF",
  "parameters": { "conditions": { "options": { "caseSensitive": true, "typeValidation": "strict" },
    "combinator": "and",
    "conditions": [ { "leftValue": "={{ $json.status }}", "rightValue": "active",
      "operator": { "type": "string", "operation": "equals" } } ] } } }
```

## Switch — multi-way branch (one output port per rule)

```json
{ "type": "n8n-nodes-base.switch", "typeVersion": 3, "name": "Switch",
  "parameters": { "mode": "rules", "rules": { "values": [
    { "conditions": { "combinator": "and", "conditions": [
      { "leftValue": "={{ $json.type }}", "rightValue": "a",
        "operator": { "type": "string", "operation": "equals" } } ] },
      "outputKey": "A" } ] } } }
```

## Filter — drop items that don't match (single output)

```json
{ "type": "n8n-nodes-base.filter", "typeVersion": 2, "name": "Filter",
  "parameters": { "conditions": { "combinator": "and", "conditions": [
    { "leftValue": "={{ $json.amount }}", "rightValue": 100,
      "operator": { "type": "number", "operation": "gt" } } ] } } }
```

## Merge — combine branches

```json
{ "type": "n8n-nodes-base.merge", "typeVersion": 3, "name": "Merge",
  "parameters": { "mode": "combine", "combineBy": "combineByPosition" } }
```
Modes: `append` (stack), `combine` (join by field/position), `chooseBranch`. A
Merge node has multiple **inputs**; target the right one with the connection
`index` (0 = first input, 1 = second).

## Loop Over Items (Split in Batches) — iterate in chunks

```json
{ "type": "n8n-nodes-base.splitInBatches", "typeVersion": 3, "name": "Loop Over Items",
  "parameters": { "batchSize": 10, "options": {} } }
```
Has two outputs: `main[0]` = "done", `main[1]` = "loop" (wire the loop body back
into this node). See `flow-logic.md` for the wiring pattern.

## Wait — pause execution

```json
{ "type": "n8n-nodes-base.wait", "typeVersion": 1.1, "name": "Wait",
  "parameters": { "resume": "timeInterval", "amount": 5, "unit": "minutes" } }
```

## Respond to Webhook — custom HTTP response

```json
{ "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "name": "Respond to Webhook",
  "parameters": { "respondWith": "json", "responseBody": "={{ JSON.stringify($json) }}" } }
```

## Popular integration nodes (need credentials)

Use these `type`s; look up the exact resource/operation parameters on the node's
docs page when building.

- Google Sheets: `n8n-nodes-base.googleSheets` (operations: append, read, update).
- Gmail: `n8n-nodes-base.gmail`; Slack: `n8n-nodes-base.slack`; Telegram:
  `n8n-nodes-base.telegram`; Discord: `n8n-nodes-base.discord`.
- Notion: `n8n-nodes-base.notion`; Airtable: `n8n-nodes-base.airtable`.
- Postgres: `n8n-nodes-base.postgres`; MySQL: `n8n-nodes-base.mySql`.
- Email send (SMTP): `n8n-nodes-base.emailSend`; RSS: `n8n-nodes-base.rssFeedRead`.

Most integration nodes follow a `resource` + `operation` pattern, e.g. Slack
`{ "resource": "message", "operation": "post", "channel": "...", "text": "..." }`.
When unsure of a node's operations, fetch its docs page or pull a real export.
