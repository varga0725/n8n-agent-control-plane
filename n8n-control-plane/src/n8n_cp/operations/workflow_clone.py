"""Operation: workflow_clone (spec 5.5) — copy a workflow (inactive), optionally
into another project, reusing credential references."""
from __future__ import annotations

from ..core import backup as backup_mod
from ..tools import run_tool
from ._util import OpResult, unwrap


def workflow_clone(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("workflow_clone")
    wid = params.get("id")
    if not wid:
        return r.fail("bad_params", "Requires 'id' of the source workflow.").finish()
    env = run_tool("n8n_workflow_get", {"id": wid}, client=client)
    if not env.get("success"):
        return r.fail("fetch_failed", "Could not fetch source.", detail=env.get("error")).finish()
    src = unwrap(env)
    body = backup_mod.restore_payload({"workflow": src},
                                      new_name=params.get("name") or f"{src.get('name')} (copy)")
    cred_refs = [n.get("credentials") for n in body.get("nodes", []) if n.get("credentials")]
    if cred_refs:
        r.warn("Clone reuses the source's credential references; ensure they are "
               "accessible in the target project.")
    r.step("prepare_clone", name=body["name"], credentialRefs=len(cred_refs))
    create = run_tool("n8n_workflow_create", {"body": body}, client=client,
                      dry_run=dry_run, confirm_token=confirm_token)
    r.step("create", status="ok" if create.get("success") else "blocked")
    r.data["created"] = create
    new_id = (unwrap(create) or {}).get("id") if create.get("success") else None
    if new_id and params.get("projectId"):
        tr = run_tool("n8n_workflow_transfer",
                      {"id": new_id, "body": {"destinationProjectId": params["projectId"]}},
                      client=client, dry_run=dry_run, confirm_token=params.get("transfer_token"))
        r.step("transfer", status="ok" if tr.get("success") else "blocked")
        r.data["transfer"] = tr
    r.success = create.get("success", False) or dry_run
    return r.finish(newWorkflowId=new_id, active=False)
