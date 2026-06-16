"""Operation: workflow_restore (spec 5.4) — recreate/update a workflow from a
backup file, with a pre-restore diff when the target still exists."""
from __future__ import annotations

from ..core import backup as backup_mod
from ..core.diff import workflow_diff
from ..tools import run_tool
from ._util import OpResult, unwrap


def workflow_restore(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("workflow_restore")
    path = params.get("path")
    if not path:
        return r.fail("bad_params", "Requires 'path' to a backup file.").finish()
    try:
        bk = backup_mod.load_backup(path)
    except OSError as e:
        return r.fail("io_error", f"Cannot read backup: {e}").finish()
    body = backup_mod.restore_payload(bk, new_name=params.get("name"))
    r.step("load_backup", workflowId=bk.get("workflowId"), name=bk.get("name"))

    if params.get("new"):
        env = run_tool("n8n_workflow_create", {"body": body}, client=client,
                       dry_run=dry_run, confirm_token=confirm_token)
        r.step("create", status="ok" if env.get("success") else "blocked")
    else:
        wid = bk.get("workflowId")
        cur = run_tool("n8n_workflow_get", {"id": wid}, client=client)
        if cur.get("success"):
            r.step("diff", **workflow_diff(unwrap(cur), body))
        env = run_tool("n8n_workflow_update", {"id": wid, "body": body},
                       client=client, dry_run=dry_run, confirm_token=confirm_token)
        r.step("update", status="ok" if env.get("success") else "blocked")
    r.data["result"] = env
    r.success = env.get("success", False) or dry_run
    return r.finish()
