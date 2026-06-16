# Advanced Data Flow & Expressions

The things that separate a toy workflow from a robust one: how items flow and
link, and the expression tools for reshaping data across complex branches. Read
this when a workflow loops, merges, fans out, or references data from several
upstream nodes.

## The n8n data model: items

Every node receives and emits an **array of items**. Each item is
`{ "json": {...}, "binary": {...} }`. A node runs **once per input item** by
default, so "do X for each record" usually needs no explicit loop — the node
already iterates. Reach for an explicit loop only for batching/rate-limiting (see
`flow-logic.md`).

- `{{ $json.field }}` — a field of the **current** item.
- `{{ $json["odd key"] }}` — bracket form for keys with spaces/dots.
- `{{ $binary.data }}` — the current item's binary property.

## Referencing other nodes

- `{{ $('Node Name').item.json.field }}` — the **linked** item from another node
  (the item paired with the current one — see item linking below).
- `{{ $('Node Name').first().json.field }}` / `.last()` — first/last item.
- `{{ $('Node Name').all() }}` — every item from that node (an array).
- `{{ $('Node Name').all()[2].json.field }}` — a specific item by index.
- `{{ $node["Node Name"].json.field }}` — older syntax, still seen in exports.

Use `$('Node Name')` (quoted) in current n8n; `$node[...]` appears in older JSON.

## Item linking / paired items (the subtle one)

When you reference `$('Earlier Node').item`, n8n needs to know *which* of that
node's items pairs with the current one. This is **paired-item** tracking. Most
built-in nodes maintain it automatically. Two places it bites:

1. **Code node**: when you build new items, preserve linking by returning
   `pairedItem`:
   ```js
   return $input.all().map((item, i) => ({
     json: { ...item.json, score: item.json.a + item.json.b },
     pairedItem: { item: i },
   }));
   ```
   Without `pairedItem`, downstream `$('X').item` lookups can fail with
   "Paired item data unavailable".

2. **After a Merge or aggregation**: linking may be ambiguous; prefer carrying
   the fields you need forward (e.g. with a Set node) rather than reaching back
   across the merge.

If you hit "Can't get data for expression / paired item", the fix is almost
always: set `pairedItem` in your Code node, or carry the value forward explicitly.

## Expression toolbox

- **Dates (Luxon)**: `{{ $now }}`, `{{ $today }}`,
  `{{ $now.plus({days: 7}).toISO() }}`, `{{ $now.toFormat('yyyy-LL-dd') }}`,
  `{{ DateTime.fromISO($json.ts).toRelative() }}`.
- **Numbers/strings**: standard JS — `{{ $json.price * 1.27 }}`,
  `{{ $json.name.trim().toLowerCase() }}`, `{{ $json.tags.join(', ') }}`.
- **JMESPath** for digging into nested JSON:
  `{{ $jmespath($json, "items[?qty > `0`].sku") }}`.
- **Conditionals**: `{{ $json.qty > 0 ? 'in stock' : 'backorder' }}`.
- **Build JSON for an HTTP body**:
  `={{ JSON.stringify({ id: $json.id, lines: $json.items.length }) }}`.
- **Context vars**: `{{ $itemIndex }}`, `{{ $runIndex }}`,
  `{{ $execution.id }}`, `{{ $workflow.id }}`, `{{ $vars.MY_VAR }}` (instance
  variables), `{{ $env.SOME_ENV }}` (if enabled).
- **Loop context** (inside Split in Batches body): `{{ $runIndex }}` increments
  per batch; `{{ $('Loop Over Items').context["noItemsLeft"] }}` is rarely needed.

## Reshaping data — which node

- **Set / Edit Fields** — add/rename/cast a few fields (declarative, no code).
- **Code** — arbitrary transforms, especially many-to-one or one-to-many.
- **Split Out** — turn one item containing an array into one item per element
  (e.g. `lineItems` → individual line items). Essential before looping over a
  nested array (a webhook delivers ONE item; Split Out expands it).
- **Aggregate** — the inverse: collapse many items into one (lists, sums).
- **Item Lists / Summarize** — group, sort, dedupe, aggregate by field.

A very common complex-flow shape: `Webhook (1 item with array)` → `Split Out`
(N items) → `Loop Over Items` (batches) → process → `Aggregate` (back to 1) →
respond. Forgetting the Split Out is the #1 reason a "loop over line items" loops
over the whole order instead.

## Multi-input referencing

After a **Merge**, downstream nodes see the merged items. To pull a field that
existed only on one branch, either merge by a matching key (so the field rides
along) or carry it with a Set node *before* the merge. Don't rely on reaching
back through `$('PreMergeNode')` after a merge — paired linking is unreliable
there.
