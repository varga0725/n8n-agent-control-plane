"""Operation: workflow_backup (spec 5.4) — full JSON + metadata to disk."""
from __future__ import annotations

from ..core import backup as backup_mod
from ..tools import run_tool
from ._util import OpResult, unwrap


def workflow_backup(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("workflow_backup")
    wid = params.get("id")
    if not wid:
        return r.fail("bad_params", "Requires 'id'.").finish()
    env = run_tool("n8n_workflow_get", {"id": wid}, client=client)
    if not env.get("success"):
        return r.fail("fetch_failed", "Could not fetch workflow.", detail=env.get("error")).finish()
    wf = unwrap(env)
    tags_env = run_tool("n8n_workflow_get_tags", {"id": wid}, client=client)
    extra = {"tags": unwrap(tags_env) if tags_env.get("success") else None}
    bk = backup_mod.backup_workflow(wf, client.config.backup_dir, extra=extra)
    r.step("backup", **bk)
    return r.finish(**bk)
