"""Workflow backup / restore to the local filesystem.

A backup is the full workflow JSON plus metadata (tags, project, version id,
credential *references* with secrets stripped) written under N8N_BACKUP_DIR.
Backups are mandatory before any workflow update or delete (enforced by the
operations layer). Restore reads a backup file and hands back a clean payload
ready for create/update.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

from .redaction import redact

# Fields the API rejects on create/update — stripped from restore payloads.
READONLY = {"id", "active", "createdAt", "updatedAt", "tags", "shared",
            "versionId", "triggerCount", "meta", "homeProject"}


def _cred_reference_only(wf: dict) -> list[dict]:
    refs = []
    for n in wf.get("nodes") or []:
        for ctype, ref in (n.get("credentials") or {}).items():
            rid = ref.get("id") if isinstance(ref, dict) else None
            name = ref.get("name") if isinstance(ref, dict) else ref
            refs.append({"node": n.get("name"), "type": ctype,
                         "id": rid, "name": name})
    return refs


def backup_workflow(workflow: dict, backup_dir: str, *,
                    extra: Optional[dict] = None) -> dict:
    """Persist a workflow snapshot. Returns metadata incl. the file path."""
    wf = workflow.get("data", workflow) if isinstance(workflow, dict) else workflow
    wid = str(wf.get("id", "unknown"))
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(backup_dir, exist_ok=True)
    path = os.path.join(backup_dir, f"workflow-{wid}-{ts}.json")

    record = {
        "backupVersion": 1,
        "takenAt": datetime.now(timezone.utc).isoformat(),
        "workflowId": wid,
        "name": wf.get("name"),
        "active": wf.get("active"),
        "versionId": wf.get("versionId"),
        "tags": wf.get("tags"),
        "project": wf.get("homeProject") or wf.get("project"),
        "credentialReferences": _cred_reference_only(wf),
        # Secrets are referenced, not embedded, so the workflow body is safe; we
        # still redact defensively in case a node parameter holds a literal.
        "workflow": redact(wf),
        "extra": extra or {},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=str)
    return {"path": path, "workflowId": wid, "takenAt": record["takenAt"],
            "name": record["name"]}


def load_backup(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def restore_payload(backup: dict, *, new_name: Optional[str] = None) -> dict:
    """Turn a backup into a clean create/update body (read-only fields removed)."""
    wf = backup.get("workflow", backup)
    wf = wf.get("data", wf)
    body = {k: v for k, v in wf.items() if k not in READONLY}
    body.setdefault("settings", {})
    if new_name:
        body["name"] = new_name
    return body
