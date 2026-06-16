"""Operation: workflow_migration (spec section 3 file tree).

Migrate a workflow to another project safely: back it up, verify its credential
references, then transfer (production-impact, gated). Unlike clone, this MOVES the
original rather than duplicating it.
"""
from __future__ import annotations

from ..core import backup as backup_mod
from ..tools import run_tool
from ._util import OpResult, unwrap


def workflow_migration(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("workflow_migration")
    wid = params.get("id")
    dest = params.get("destinationProjectId") or params.get("projectId")
    if not wid or not dest:
        return r.fail("bad_params", "Requires 'id' and 'destinationProjectId'.").finish()

    env = run_tool("n8n_workflow_get", {"id": wid}, client=client)
    if not env.get("success"):
        return r.fail("fetch_failed", "Could not fetch workflow.", detail=env.get("error")).finish()
    wf = unwrap(env)
    bk = backup_mod.backup_workflow(wf, client.config.backup_dir)
    r.step("backup", path=bk["path"], active=wf.get("active"))

    cred_refs = [n.get("credentials") for n in wf.get("nodes", []) if n.get("credentials")]
    if cred_refs:
        r.warn("Workflow uses credentials — confirm they exist/are shared in the "
               "destination project, or the moved workflow will fail.")
    if wf.get("active"):
        r.warn("Workflow is ACTIVE — moving it is production-impact.")

    tr = run_tool("n8n_workflow_transfer",
                  {"id": wid, "body": {"destinationProjectId": dest}},
                  client=client, dry_run=dry_run, confirm_token=confirm_token)
    r.step("transfer", status="ok" if tr.get("success") else "blocked",
           riskLevel=tr.get("riskLevel"))
    r.data["transfer"] = tr
    r.success = tr.get("success", False) or dry_run
    return r.finish(workflowId=wid, destinationProjectId=dest, backup=bk["path"])
