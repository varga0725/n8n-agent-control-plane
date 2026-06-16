"""Operation: safe_workflow_deploy (spec 5.1).

Update an existing workflow safely: capability -> fetch current -> backup ->
validate -> diff -> impact -> update (gated) -> read back -> validate -> activate
(separately gated) -> rollback on failure.
"""
from __future__ import annotations

from ..core import backup as backup_mod
from ..core.diff import workflow_diff
from ..core.validation import validate_workflow_body
from ..tools import run_tool
from ._util import OpResult, unwrap


def safe_workflow_deploy(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("safe_workflow_deploy")
    wid = params.get("id")
    new_body = params.get("workflow")
    if not wid or not isinstance(new_body, dict):
        return r.fail("bad_params", "Requires 'id' and 'workflow' (object).").finish()

    cur_env = run_tool("n8n_workflow_get", {"id": wid}, client=client)
    if not cur_env.get("success"):
        return r.fail("fetch_failed", "Could not fetch current workflow.",
                      detail=cur_env.get("error")).finish()
    current = unwrap(cur_env)
    r.step("fetch_current", id=wid, active=current.get("active"))

    bk = backup_mod.backup_workflow(current, client.config.backup_dir)
    r.step("backup", path=bk["path"])

    problems = validate_workflow_body(new_body)
    if problems:
        return r.fail("validation_error", "; ".join(problems)).finish()
    r.step("validate", ok=True)

    diff = workflow_diff(current, new_body)
    r.step("diff", **diff)
    impact = {"diff": diff, "currentlyActive": current.get("active"), "backup": bk["path"]}
    if diff["triggerOrWebhookOrScheduleChanges"]:
        r.warn("Trigger/webhook/schedule changes detected — review external impact.")
    if diff["credentialRefsRemoved"]:
        r.warn("Credential references removed — downstream nodes may lose auth.")

    upd = run_tool("n8n_workflow_update", {"id": wid, "body": new_body},
                   client=client, dry_run=dry_run, confirm_token=confirm_token)
    r.step("update", status="ok" if upd.get("success") else "blocked",
           riskLevel=upd.get("riskLevel"))
    if not upd.get("success"):
        r.data["update"] = upd
        if upd.get("error", {}).get("type") in ("confirmation_required", "policy_blocked"):
            r.warn("Update requires confirmation. Show impact, then re-run with the "
                   "confirmationToken in data.update.error.details.")
            return r.finish(impact=impact)
        return r.fail("update_failed", "Workflow update failed; original is intact "
                      f"(backup at {bk['path']}).", detail=upd.get("error")).finish(impact=impact)

    if dry_run:
        return r.finish(impact=impact, dryRun=True)

    back_env = run_tool("n8n_workflow_get", {"id": wid}, client=client)
    readback = unwrap(back_env)
    rb_problems = validate_workflow_body(readback)
    r.step("readback_validate", ok=not rb_problems, problems=rb_problems)

    if params.get("activate"):
        act = run_tool("n8n_workflow_activate", {"id": wid}, client=client,
                       dry_run=dry_run, confirm_token=params.get("activate_token"))
        r.step("activate", status="ok" if act.get("success") else "blocked")
        r.data["activate"] = act
        if not act.get("success"):
            r.warn("Workflow updated but NOT activated (needs its own confirmation).")

    return r.finish(workflowId=wid, backup=bk["path"], diff=diff)
