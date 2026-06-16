#!/usr/bin/env python3
"""Fetch a machine-readable n8n node schema (offline-capable, no live instance).

Unlike fetch_node_template.py (which reads YOUR instance), this pulls the exact
parameter schema for a node from the community-maintained, auto-updated schema set
(yigitkonur/n8n-schema-generator). Use it to learn a node's parameters,
availableVersions, defaults and required fields WITHOUT a running n8n.

Usage:
  python3 fetch_node_schema.py --type n8n-nodes-base.httpRequest
  python3 fetch_node_schema.py --type if --params-only
  python3 fetch_node_schema.py --list                       # all node names
  python3 fetch_node_schema.py --search slack
  python3 fetch_node_schema.py --credential slackApi
  python3 fetch_node_schema.py --cache ./n8n-schemas --type postgres   # save locally

Note: covers n8n-nodes-base nodes. LangChain/AI nodes
(@n8n/n8n-nodes-langchain.*) are a separate package and are not in this set —
for those, use fetch_node_template.py against a live instance, or the n8n-mcp
connector (see references/node-schemas.md).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import n8n_schemas as ns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", help="node type (full or short), e.g. n8n-nodes-base.if or if")
    ap.add_argument("--credential", help="credential type name, e.g. slackApi")
    ap.add_argument("--list", action="store_true", help="list all available node names")
    ap.add_argument("--search", help="filter the node list by substring")
    ap.add_argument("--params-only", action="store_true",
                    help="print just the parameter names + versions")
    ap.add_argument("--cache", help="also save fetched schema(s) into this dir")
    a = ap.parse_args()

    if a.list or a.search:
        idx = ns.load_index(a.cache)
        if not idx:
            sys.exit("Could not load node index (no network / no cache).")
        names = idx.get("nodes", [])
        if a.search:
            names = [n for n in names if a.search.lower() in n.lower()]
        print("\n".join(names))
        print(f"\n({len(names)} nodes, total {idx.get('totalNodes')})", file=sys.stderr)
        return

    if a.credential:
        sch = ns.load_credential_schema(a.credential, a.cache)
        if not sch:
            sys.exit(f"No schema for credential '{a.credential}'.")
        _maybe_cache(a.cache, "credentials", a.credential, sch)
        print(json.dumps(sch, indent=2))
        return

    if not a.type:
        sys.exit("Pass --type, --credential, --list, or --search.")

    sch = ns.load_node_schema(a.type, a.cache)
    if not sch:
        sys.exit(f"No schema found for '{a.type}'. If it's a LangChain/AI or "
                 f"community node, use fetch_node_template.py against a live "
                 f"instance instead (see references/node-schemas.md).")
    _maybe_cache(a.cache, "nodes", ns.short_name(a.type), sch)

    if a.params_only:
        print(f"# {sch.get('displayName')} ({a.type})")
        print(f"availableVersions: {ns.available_versions(sch)} "
              f"(default {sch.get('defaultVersion')})")
        for p in sch.get("properties", []):
            req = " [required]" if p.get("required") else ""
            print(f"  - {p.get('name')}: {p.get('type')}{req}")
        return

    print(json.dumps(sch, indent=2))


def _maybe_cache(cache_dir, sub, name, data):
    if not cache_dir:
        return
    d = os.path.join(cache_dir, sub)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{name}.json"), "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
