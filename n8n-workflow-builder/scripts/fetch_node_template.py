#!/usr/bin/env python3
"""Pull EXACT, current node JSON from a live n8n instance to use as a template.

The single hardest part of authoring complex workflows is getting each node's
parameter shape and typeVersion exactly right for the target n8n version. Node
parameter schemas are not in the API spec — the most reliable source is a real
export from the instance itself. This helper fetches workflows over the Public API
and extracts the nodes you care about, so you can copy their precise structure.

Reads N8N_BASE_URL and N8N_API_KEY from the environment (same as n8n_api.py).

Usage:
  # Show the exact JSON of every Postgres node found across your workflows
  python3 fetch_node_template.py --type n8n-nodes-base.postgres

  # Limit to one workflow, list all its node types
  python3 fetch_node_template.py --workflow 128 --list-types

  # Grab a whole workflow as a starting template (read-only fields stripped)
  python3 fetch_node_template.py --workflow 128 --as-template
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

READONLY = {"id", "active", "createdAt", "updatedAt", "tags", "versionId",
            "triggerCount", "shared", "meta", "homeProject"}


def _cfg():
    base = os.environ.get("N8N_BASE_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        sys.exit("Set N8N_BASE_URL and N8N_API_KEY (the instance to read templates from).")
    if not base.endswith("/api/v1"):
        base += "/api/v1"
    return base, key


def _get(path, query=None):
    base, key = _cfg()
    url = base + path
    if query:
        url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
    req = urllib.request.Request(url, method="GET")
    req.add_header("X-N8N-API-KEY", key)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} on GET {path}: {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        sys.exit(f"Connection error: {e.reason}")


def _workflows(workflow_id=None):
    if workflow_id:
        wf = _get(f"/workflows/{workflow_id}")
        return [wf.get("data", wf)]
    out, cursor = [], None
    while True:
        page = _get("/workflows", {"limit": 100, "cursor": cursor})
        out.extend(page.get("data", []))
        cursor = page.get("nextCursor")
        if not cursor:
            break
    return out


def _strip(node: dict) -> dict:
    """Keep the fields that define a node template; drop instance-specifics."""
    n = {k: node.get(k) for k in ("parameters", "type", "typeVersion", "name", "position")}
    if node.get("credentials"):
        # keep credential TYPE keys but blank the ids/names (they're per-instance)
        n["credentials"] = {ct: {"id": "<your-credential-id>", "name": "<name>"}
                            for ct in node["credentials"]}
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", help="node type to extract, e.g. n8n-nodes-base.postgres")
    ap.add_argument("--workflow", help="restrict to one workflow id")
    ap.add_argument("--list-types", action="store_true", help="just list node types present")
    ap.add_argument("--as-template", action="store_true",
                    help="output the whole workflow as a clean create/update body")
    a = ap.parse_args()

    wfs = _workflows(a.workflow)

    if a.as_template and a.workflow:
        wf = wfs[0]
        body = {k: v for k, v in wf.items() if k not in READONLY}
        body.setdefault("settings", {})
        print(json.dumps(body, indent=2))
        return

    if a.list_types:
        types = {}
        for wf in wfs:
            for n in wf.get("nodes", []):
                types.setdefault(n.get("type"), n.get("typeVersion"))
        for t, v in sorted(types.items()):
            print(f"{t}\tv{v}")
        return

    if not a.type:
        sys.exit("Pass --type, --list-types, or --workflow ... --as-template")

    found = []
    for wf in wfs:
        for n in wf.get("nodes", []):
            if n.get("type") == a.type:
                found.append({"fromWorkflow": wf.get("name"), "template": _strip(n)})
    if not found:
        print(f"No nodes of type {a.type} found in {'that workflow' if a.workflow else 'any workflow'}.")
        return
    # de-dup by (typeVersion, param keys) to show distinct shapes
    print(json.dumps(found, indent=2))


if __name__ == "__main__":
    main()
