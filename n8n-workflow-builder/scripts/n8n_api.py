#!/usr/bin/env python3
"""Thin CLI over the n8n public REST API (/api/v1).

Reads credentials from the environment:
    N8N_BASE_URL  e.g. https://n8n.example.com   (no trailing /api/v1)
    N8N_API_KEY   the API key from Settings -> n8n API

Uses only the Python standard library (urllib) so it runs anywhere.

Examples:
    python3 n8n_api.py list
    python3 n8n_api.py list --active
    python3 n8n_api.py get <id> > template.json
    python3 n8n_api.py create workflow.json
    python3 n8n_api.py create workflow.json --activate
    python3 n8n_api.py update <id> workflow.json
    python3 n8n_api.py activate <id>
    python3 n8n_api.py deactivate <id>
    python3 n8n_api.py delete <id>
    python3 n8n_api.py executions --workflow <id> --status error
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

READONLY = {"id", "active", "createdAt", "updatedAt", "tags",
            "shared", "versionId", "triggerCount", "meta"}


def _cfg():
    base = os.environ.get("N8N_BASE_URL", "").rstrip("/")
    key = os.environ.get("N8N_API_KEY", "")
    if not base or not key:
        sys.exit("Set N8N_BASE_URL and N8N_API_KEY environment variables.")
    return base, key


def request(method, path, body=None, query=None):
    base, key = _cfg()
    url = f"{base}/api/v1{path}"
    if query:
        url += "?" + urllib.parse.urlencode({k: v for k, v in query.items()
                                             if v is not None})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-N8N-API-KEY", key)
    req.add_header("Accept", "application/json")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        sys.exit(f"HTTP {e.code} {e.reason} on {method} {path}\n{detail}")
    except urllib.error.URLError as e:
        sys.exit(f"Connection error: {e.reason}")


def clean(wf):
    """Strip read-only fields so a fetched workflow can be re-created/updated."""
    if "data" in wf and "nodes" not in wf:
        wf = wf["data"]
    body = {k: v for k, v in wf.items() if k not in READONLY}
    body.setdefault("settings", {})
    return body


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    p = argparse.ArgumentParser(description="n8n public API CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list")
    pl.add_argument("--active", action="store_true")
    pl.add_argument("--limit", type=int, default=100)

    pg = sub.add_parser("get"); pg.add_argument("id")

    pc = sub.add_parser("create")
    pc.add_argument("file"); pc.add_argument("--activate", action="store_true")

    pu = sub.add_parser("update")
    pu.add_argument("id"); pu.add_argument("file")

    for name in ("activate", "deactivate", "delete"):
        sp = sub.add_parser(name); sp.add_argument("id")

    pe = sub.add_parser("executions")
    pe.add_argument("--workflow"); pe.add_argument("--status")
    pe.add_argument("--limit", type=int, default=20)

    a = p.parse_args()

    if a.cmd == "list":
        q = {"limit": a.limit}
        if a.active:
            q["active"] = "true"
        res = request("GET", "/workflows", query=q)
        for w in res.get("data", []):
            print(f"{w['id']}\t{'ON ' if w.get('active') else 'off'}\t{w['name']}")

    elif a.cmd == "get":
        print(json.dumps(request("GET", f"/workflows/{a.id}"), indent=2))

    elif a.cmd == "create":
        body = clean(load(a.file))
        res = request("POST", "/workflows", body=body)
        wid = res.get("id") or res.get("data", {}).get("id")
        print(f"Created workflow id: {wid}")
        if a.activate and wid:
            request("POST", f"/workflows/{wid}/activate")
            print("Activated.")

    elif a.cmd == "update":
        body = clean(load(a.file))
        res = request("PUT", f"/workflows/{a.id}", body=body)
        print(f"Updated workflow id: {res.get('id', a.id)}")

    elif a.cmd in ("activate", "deactivate"):
        request("POST", f"/workflows/{a.id}/{a.cmd}")
        print(f"{a.cmd}d {a.id}")

    elif a.cmd == "delete":
        request("DELETE", f"/workflows/{a.id}")
        print(f"Deleted {a.id}")

    elif a.cmd == "executions":
        q = {"limit": a.limit, "workflowId": a.workflow, "status": a.status}
        res = request("GET", "/executions", query=q)
        for e in res.get("data", []):
            print(f"{e['id']}\t{e.get('status')}\t{e.get('startedAt')}\t"
                  f"wf={e.get('workflowId')}")


if __name__ == "__main__":
    main()
