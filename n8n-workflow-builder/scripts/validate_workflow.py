#!/usr/bin/env python3
"""Structural validator for n8n workflow JSON.

Catches the mistakes that make a workflow import but misbehave: connections that
point at nonexistent nodes, duplicate node names (which silently break wiring),
malformed connection nesting, missing required fields, missing triggers, and
read-only fields left in the body.

Usage:
    python3 validate_workflow.py workflow.json
Exit code 0 = valid (warnings allowed), 1 = errors found, 2 = bad input.
"""
import json
import sys

READONLY = {"id", "active", "createdAt", "updatedAt", "tags"}
TRIGGER_HINTS = ("trigger", "webhook", "cron", "manualtrigger", "scheduletrigger",
                 "errortrigger", "chattrigger")


def is_trigger(node_type: str) -> bool:
    t = node_type.lower()
    return any(h in t for h in TRIGGER_HINTS)


def validate(wf: dict):
    errors, warnings = [], []

    # Required top-level keys
    for key in ("name", "nodes", "connections", "settings"):
        if key not in wf:
            errors.append(f"Missing required top-level field: '{key}'")
    if errors:
        return errors, warnings

    for f in READONLY:
        if f in wf:
            warnings.append(f"Read-only field '{f}' present — strip it before "
                            f"POST/PUT to the API (the script does this for you).")

    nodes = wf.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append("'nodes' must be a non-empty array")
        return errors, warnings

    names, ids, trigger_found = set(), set(), False
    for i, n in enumerate(nodes):
        where = f"node[{i}]"
        for f in ("name", "type", "typeVersion", "position"):
            if f not in n:
                errors.append(f"{where} missing '{f}'")
        name = n.get("name")
        if name in names:
            errors.append(f"Duplicate node name '{name}' — connections key by "
                          f"name, so duplicates break wiring")
        names.add(name)
        nid = n.get("id")
        if nid is not None:
            if nid in ids:
                errors.append(f"Duplicate node id '{nid}'")
            ids.add(nid)
        pos = n.get("position")
        if not (isinstance(pos, list) and len(pos) == 2
                and all(isinstance(x, (int, float)) for x in pos)):
            errors.append(f"{where} ('{name}') position must be [x, y] numbers")
        if n.get("type") and is_trigger(n["type"]):
            trigger_found = True

    if not trigger_found:
        warnings.append("No trigger node found (manual/webhook/schedule/app "
                        "trigger). Fine for a sub-workflow, otherwise add one.")

    # Connections
    conns = wf.get("connections", {})
    if not isinstance(conns, dict):
        errors.append("'connections' must be an object")
        return errors, warnings

    referenced = set()
    for src, outputs in conns.items():
        if src not in names:
            errors.append(f"Connection source '{src}' is not a known node name")
        if not isinstance(outputs, dict):
            errors.append(f"Connections for '{src}' must be an object "
                          f"(e.g. {{'main': [[...]]}})")
            continue
        for ctype, ports in outputs.items():
            if not isinstance(ports, list):
                errors.append(f"'{src}'.{ctype} must be an array of ports")
                continue
            for p_i, port in enumerate(ports):
                if not isinstance(port, list):
                    errors.append(f"'{src}'.{ctype}[{p_i}] must be an array of "
                                  f"targets (array-of-arrays nesting)")
                    continue
                for tgt in port:
                    if not isinstance(tgt, dict) or "node" not in tgt:
                        errors.append(f"'{src}'.{ctype}[{p_i}] has a malformed "
                                      f"target (need {{node,type,index}})")
                        continue
                    if tgt["node"] not in names:
                        errors.append(f"'{src}' connects to unknown node "
                                      f"'{tgt['node']}'")
                    referenced.add(src)
                    referenced.add(tgt["node"])

    # Orphans (nodes with no connection at all, excluding lone triggers)
    for n in nodes:
        nm = n.get("name")
        if nm not in referenced and len(nodes) > 1:
            warnings.append(f"Node '{nm}' has no connections — likely orphaned")

    return errors, warnings


def deep_check(wf: dict, schema_dir=None):
    """Param-level validation against machine-readable node schemas.

    Checks each node's typeVersion and top-level parameters against the
    community schema set (see n8n_schemas.py). Degrades gracefully: nodes with no
    available schema (LangChain/AI, community, or offline) are noted, not failed.
    Returns (errors, warnings, checked_count)."""
    try:
        import n8n_schemas as ns
    except ImportError:
        return [], ["--deep: n8n_schemas.py not found next to this script."], 0

    errors, warnings, checked = [], [], 0
    for node in wf.get("nodes", []):
        ntype = node.get("type", "")
        schema = ns.load_node_schema(ntype, schema_dir)
        if not schema:
            warnings.append(f"no schema for '{node.get('name')}' ({ntype}) — "
                            f"skipped deep check (LangChain/community/offline).")
            continue
        checked += 1
        for level, msg in ns.check_node(node, schema):
            (errors if level == "error" else warnings).append("deep: " + msg)
    return errors, warnings, checked


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Validate an n8n workflow JSON.")
    ap.add_argument("workflow", help="path to the workflow .json")
    ap.add_argument("--deep", action="store_true",
                    help="also check typeVersion/params against node schemas")
    ap.add_argument("--schema-dir", help="local dir of cached node schemas "
                    "(else fetched from GitHub); see fetch_node_schema.py --cache")
    a = ap.parse_args()

    try:
        with open(a.workflow) as f:
            wf = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Cannot read/parse JSON: {e}")
        sys.exit(2)

    # Accept either a bare workflow or an API response wrapped in {"data": {...}}
    if isinstance(wf, dict) and "data" in wf and "nodes" not in wf:
        wf = wf["data"]

    errors, warnings = validate(wf)
    deep_checked = None
    if a.deep and not errors:
        d_err, d_warn, deep_checked = deep_check(wf, a.schema_dir)
        errors += d_err
        warnings += d_warn

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\n✗ {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    suffix = f", deep-checked {deep_checked} node(s)" if deep_checked is not None else ""
    print(f"\n✓ Valid workflow ({len(wf['nodes'])} nodes, "
          f"{len(warnings)} warning(s){suffix})")
    sys.exit(0)


if __name__ == "__main__":
    main()
