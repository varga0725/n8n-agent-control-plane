"""Workflow diffing.

Before any workflow update we compute a structural diff so the human sees
exactly what changes: nodes added/removed/modified, connection changes, and —
called out specially because they carry production impact — trigger / webhook /
schedule changes and credential-reference changes.
"""
from __future__ import annotations

from typing import Any


def _nodes_by_name(wf: dict) -> dict[str, dict]:
    return {n.get("name"): n for n in (wf.get("nodes") or [])}


def _is_trigger(node: dict) -> bool:
    t = (node.get("type") or "").lower()
    return any(h in t for h in ("trigger", "webhook", "cron", "schedule"))


def _cred_refs(wf: dict) -> set[str]:
    refs = set()
    for n in wf.get("nodes") or []:
        for ctype, ref in (n.get("credentials") or {}).items():
            rid = ref.get("id") if isinstance(ref, dict) else ref
            refs.add(f"{n.get('name')}::{ctype}::{rid}")
    return refs


def workflow_diff(old: dict, new: dict) -> dict:
    old_n, new_n = _nodes_by_name(old), _nodes_by_name(new)
    old_names, new_names = set(old_n), set(new_n)

    added = sorted(new_names - old_names)
    removed = sorted(old_names - new_names)
    modified = []
    for name in sorted(old_names & new_names):
        if _node_signature(old_n[name]) != _node_signature(new_n[name]):
            modified.append(name)

    trigger_changes = sorted(
        n for n in (added + removed + modified)
        if _is_trigger(new_n.get(n, old_n.get(n, {})))
    )

    cred_added = sorted(_cred_refs(new) - _cred_refs(old))
    cred_removed = sorted(_cred_refs(old) - _cred_refs(new))

    conn_changed = (old.get("connections") != new.get("connections"))
    active_change = None
    if old.get("active") is not None and new.get("active") is not None:
        if old.get("active") != new.get("active"):
            active_change = {"from": old.get("active"), "to": new.get("active")}

    return {
        "nodesAdded": added,
        "nodesRemoved": removed,
        "nodesModified": modified,
        "connectionsChanged": conn_changed,
        "triggerOrWebhookOrScheduleChanges": trigger_changes,
        "credentialRefsAdded": cred_added,
        "credentialRefsRemoved": cred_removed,
        "activeStatusChange": active_change,
        "summary": _summarize(added, removed, modified, conn_changed,
                              trigger_changes, cred_added, cred_removed),
    }


def _node_signature(node: dict) -> Any:
    import json
    return json.dumps({
        "type": node.get("type"),
        "typeVersion": node.get("typeVersion"),
        "parameters": node.get("parameters"),
        "credentials": node.get("credentials"),
        "position": node.get("position"),
        "disabled": node.get("disabled"),
    }, sort_keys=True, default=str)


def _summarize(added, removed, modified, conn, triggers, cadd, crem) -> str:
    parts = []
    if added:    parts.append(f"+{len(added)} node(s)")
    if removed:  parts.append(f"-{len(removed)} node(s)")
    if modified: parts.append(f"~{len(modified)} node(s)")
    if conn:     parts.append("connections changed")
    if triggers: parts.append(f"{len(triggers)} trigger/webhook/schedule change(s)")
    if cadd or crem: parts.append(f"credential refs Δ (+{len(cadd)}/-{len(crem)})")
    return ", ".join(parts) if parts else "no structural changes"
