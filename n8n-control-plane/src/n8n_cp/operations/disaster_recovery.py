"""Operation: disaster_recovery — back up every workflow on the instance to disk
(read-only against the API; local file writes only). Restore is per-file via
workflow_restore."""
from __future__ import annotations

from ..core import backup as backup_mod
from ..tools import run_tool
from ._util import OpResult, unwrap
from ._instance_common import safe_list


def disaster_recovery(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("disaster_recovery")
    wfs, err = safe_list(client, "n8n_workflow_list", {"limit": params.get("limit", 250)})
    if wfs is None:
        return r.fail("list_failed", "Could not list workflows.", detail=err).finish()
    r.step("enumerate", workflows=len(wfs))
    saved = []
    for w in wfs:
        full = run_tool("n8n_workflow_get", {"id": w.get("id")}, client=client)
        if full.get("success"):
            bk = backup_mod.backup_workflow(unwrap(full), client.config.backup_dir)
            saved.append(bk["path"])
    r.step("backup", saved=len(saved))
    return r.finish(backedUp=len(saved), files=saved[:50], backupDir=client.config.backup_dir)
