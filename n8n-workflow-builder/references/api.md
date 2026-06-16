# n8n Public REST API

The public API is how you deploy workflows programmatically. It is distinct from
the internal `/rest/` API the editor uses — always target `/api/v1/`.

## Base URL and authentication

```
Base:   <N8N_BASE_URL>/api/v1
Header: X-N8N-API-KEY: <api-key>
Accept: application/json
```

- `<N8N_BASE_URL>` is the instance root, e.g. `https://n8n.example.com` or a
  self-hosted/Tailscale host. The user's interactive API docs live at
  `<N8N_BASE_URL>/api/v1/docs` (Swagger UI) — the authoritative, version-exact
  reference for *their* instance.
- The API key is created in the n8n UI: **Settings → n8n API → Create an API
  key**. It is not the same as a user password.
- Every request needs the `X-N8N-API-KEY` header. A missing/invalid key returns
  `401`.

The helper script reads `N8N_BASE_URL` and `N8N_API_KEY` from the environment:

```bash
export N8N_BASE_URL="https://n8n.example.com"
export N8N_API_KEY="n8n_api_xxx"
```

## Workflow endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/workflows` | List. Query: `active`, `tags`, `name`, `limit` (max 250), `cursor`, `projectId`. |
| GET | `/workflows/{id}` | Fetch one (full JSON — great as a template). |
| POST | `/workflows` | Create. Body = workflow object (`name`, `nodes`, `connections`, `settings`). |
| PUT | `/workflows/{id}` | Replace/update. Same required body fields. |
| DELETE | `/workflows/{id}` | Delete. |
| POST | `/workflows/{id}/activate` | Activate (turn on triggers). |
| POST | `/workflows/{id}/deactivate` | Deactivate. |
| PUT | `/workflows/{id}/tags` | Set tags (array of tag IDs). |
| PUT | `/workflows/{id}/transfer` | Move to another project. |

**Critical:** `active` and `tags` are read-only in the create/update body. To get
a live workflow you do two calls: `POST /workflows` then
`POST /workflows/{id}/activate`. Sending `active: true` in the create body is
ignored (and may error on strict validation).

### Create then activate (curl)

```bash
# Create
curl -sS -X POST "$N8N_BASE_URL/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  --data @workflow.json
# → response includes the new "id"

# Activate
curl -sS -X POST "$N8N_BASE_URL/api/v1/workflows/<id>/activate" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

Note: a workflow can only be activated if it has an activatable trigger (webhook,
schedule, app trigger). A manual-trigger-only workflow cannot be "active" — it
runs on demand.

## Execution endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/executions` | List. Query: `status` (`success`/`error`/`waiting`), `workflowId`, `limit`, `cursor`, `includeData`. |
| GET | `/executions/{id}` | One execution; add `?includeData=true` for full run data. |
| DELETE | `/executions/{id}` | Delete an execution record. |

The public API does **not** run a workflow on demand. To trigger a run from
outside, give the workflow a **Webhook** trigger and `POST` to its webhook URL,
or activate a schedule trigger.

## Credential endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/credentials` | Create a credential. Body: `name`, `type`, `data` (the secret fields). |
| DELETE | `/credentials/{id}` | Delete. |
| GET | `/credentials/schema/{credentialTypeName}` | Get the required fields for a credential type. |

There is **no list/get-all credentials endpoint** (by design, for security). So
when deploying a workflow that needs credentials you cannot discover existing
IDs through the API — either create the credential via `POST /credentials` and
use the returned `id` in the node, or have the user select it in the UI after
import. Use `GET /credentials/schema/{type}` to learn what `data` fields a type
needs before creating one.

## Tag endpoints

`GET /tags`, `POST /tags` (`{ "name": "..." }`), `GET/PUT/DELETE /tags/{id}`.
Assign to a workflow with `PUT /workflows/{id}/tags` (array of tag IDs).

## Pagination

List endpoints are cursor-based. The response contains `data` and `nextCursor`.
Pass `?cursor=<nextCursor>` to get the next page; `limit` caps page size
(workflows max 250). Loop until `nextCursor` is null.

```bash
curl -sS "$N8N_BASE_URL/api/v1/workflows?limit=100&cursor=$CURSOR" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

## Common status codes

`200/201` ok · `400` bad body (often a read-only field or malformed
connections) · `401` bad/missing API key · `404` workflow/credential not found ·
`500` server-side (frequently an invalid node type or typeVersion the instance
doesn't have installed).

## Using the helper script

```bash
python3 scripts/n8n_api.py list
python3 scripts/n8n_api.py get <id> > template.json
python3 scripts/n8n_api.py create workflow.json          # prints new id
python3 scripts/n8n_api.py create workflow.json --activate
python3 scripts/n8n_api.py update <id> workflow.json
python3 scripts/n8n_api.py activate <id>
python3 scripts/n8n_api.py deactivate <id>
python3 scripts/n8n_api.py delete <id>
python3 scripts/n8n_api.py executions --workflow <id> --status error
```

The script strips read-only fields automatically before create/update, so you
can round-trip a `get` output back into `create`/`update` without manual editing.
