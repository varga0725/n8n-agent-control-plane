# Complex Workflow Patterns

Real workflows branch, loop, recover from errors, and orchestrate AI. This file
points to **complete, validated, copy-paste** example workflows in
`references/examples/` and explains the wiring decisions that make each one work.
Every example passes `scripts/validate_workflow.py`. Use them as starting
skeletons — then confirm node parameters against the live instance (see
`scripts/fetch_node_template.py`), since parameter shapes drift by version.

When building anything non-trivial, the recurring lessons are: (1) connections are
arrays-of-arrays keyed by node name; (2) a node already runs once per item, so use
explicit loops only for batching; (3) a webhook delivers ONE item, so split nested
arrays before looping; (4) wire error outputs deliberately rather than letting a
run abort. See `workflow-schema.md` and `data-and-expressions.md` for the
mechanics.

## 1. Branching + batched loop + error handling
File: `examples/01-order-processing-branch-loop-error.json` (15 nodes)

An order webhook that validates, upserts a customer, processes line items in
batches, and recovers from per-item API failures:

- **Webhook** → **IF (validate)**: `main[0]` (valid) continues; `main[1]`
  (invalid) → **Respond to Webhook** 400. Two outputs, two destinations.
- **Postgres lookup** → **IF (customer exists?)**: false branch → **Insert
  Customer** → rejoins the true branch at **Split Out**.
- **Split Out** expands the order's `lineItems` array into one item each (without
  this, the loop would batch the whole order — the #1 mistake).
- **Loop Over Items** (`splitInBatches`, batchSize 10): `main[0]` = done →
  **Aggregate**; `main[1]` = loop → **Check Inventory** (HTTP).
- **Check Inventory** uses `"onError": "continueErrorOutput"`: `main[0]` success →
  back into the loop; `main[1]` error → **Slack alert** → back into the loop. A
  failed item never aborts the run.
- **Aggregate** (Code) → **Google Sheets** append → **Respond** with a summary.

This is the canonical "robust ingestion" shape: validate early, branch, loop with
isolation, recover, respond.

## 2. Paginating an API in a loop
File: `examples/02-paginating-http-loop.json` (7 nodes)

Fetch every page of a paginated API:

- **Set (Init Page)** seeds `page = 1`.
- **Loop** (`splitInBatches`, batchSize 1) drives the iteration: `main[1]` (loop)
  → **Fetch Page** (HTTP, `?page={{ $json.page }}`).
- **IF (More Pages?)** on `hasMore`: true → **Next Page** (Set `page + 1`) →
  back to **Loop**; false → empty (falls through to the loop's done output).
- **Loop** `main[0]` (done) → **Process All** (Code over `$input.all()`).

The pattern: a counter in Set, the loop body increments and re-enters, the IF's
false branch ends the loop. Swap `splitInBatches` for a direct self-loop only if
you don't need n8n's loop bookkeeping.

## 3. A global error workflow
File: `examples/03-error-workflow.json` (3 nodes)

- **Error Trigger** receives `{{ $json.workflow }}` and `{{ $json.execution }}`
  (incl. `execution.error.message` and `lastNodeExecuted`).
- **Set** formats an alert message → **Slack** posts it.

Wire it up by setting `settings.errorWorkflow` to THIS workflow's id on your other
workflows (or select it as the error workflow in their settings). One handler then
catches failures across many workflows — the standard production pattern. Swap
Slack for Email/PagerDuty as needed.

## 4. RAG AI agent (LangChain nodes + ai_* connections)
File: `examples/04-ai-rag-agent.json` (7 nodes)

A retrieval-augmented chat agent. Note the connections use `ai_*` types, not
`main` — sub-nodes attach capabilities to the agent (see `ai-nodes.md`):

- **Chat Trigger** → **AI Agent** (`main`).
- **OpenAI Chat Model** → both the **AI Agent** and the **Knowledge Base Tool**
  via `ai_languageModel` (one output port, two targets).
- **Simple Memory** → agent via `ai_memory`.
- **Embeddings OpenAI** → **Qdrant Vector Store** via `ai_embedding`.
- **Qdrant Vector Store** → **Knowledge Base Tool** via `ai_vectorStore`.
- **Knowledge Base Tool** (`toolVectorStore`) → agent via `ai_tool`.

So the agent gets a model, memory, and a knowledge-base tool backed by a vector
store that is fed by an embeddings model. Add more tools (HTTP, Code, sub-workflow)
by connecting them to the agent with additional `ai_tool` connections.

## Getting node parameters exactly right
These skeletons are structurally correct, but a node's `parameters` and
`typeVersion` can differ on your n8n version (e.g. Postgres `__rl` resource
locators, Slack channel id vs. name, the HTTP error-output field name). The most
reliable fix:

```bash
# See the exact current JSON of every Postgres node already on your instance
python3 scripts/fetch_node_template.py --type n8n-nodes-base.postgres
# Or grab a whole working workflow as a template
python3 scripts/fetch_node_template.py --workflow 128 --as-template
```

Copy those exact shapes into your new workflow. Building once in the UI and
reading it back beats guessing every time.
