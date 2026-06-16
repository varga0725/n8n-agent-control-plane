"""Operation: project_bootstrap (spec 5.6) — create a project with users, roles,
folders, tags and variables. Each access/production step is individually gated."""
from __future__ import annotations

from ..tools import run_tool
from ._util import OpResult, unwrap


def project_bootstrap(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("project_bootstrap")
    name = params.get("name")
    if not name:
        return r.fail("bad_params", "Requires project 'name'.").finish()

    proj = run_tool("n8n_project_create", {"body": {"name": name}}, client=client,
                    dry_run=dry_run, confirm_token=confirm_token)
    r.step("create_project", status="ok" if proj.get("success") else "blocked")
    if not (proj.get("success") or dry_run):
        return r.fail("project_failed", "Project creation failed.", detail=proj.get("error")).finish()
    pid = (unwrap(proj) or {}).get("id") if proj.get("success") else "<new>"

    report = {"projectId": pid, "users": [], "folders": [], "tags": [], "variables": []}
    for u in params.get("users", []) or []:
        res = run_tool("n8n_project_user_add", {"projectId": pid, "body": u},
                       client=client, dry_run=dry_run, confirm_token=u.get("token"))
        report["users"].append({"email": u.get("email"), "ok": res.get("success"),
                                "risk": res.get("riskLevel")})
    for fname in params.get("folders", []) or []:
        res = run_tool("n8n_folder_create", {"projectId": pid, "body": {"name": fname}},
                       client=client, dry_run=dry_run)
        report["folders"].append({"name": fname, "ok": res.get("success")})
    for tname in params.get("tags", []) or []:
        res = run_tool("n8n_tag_create", {"body": {"name": tname}}, client=client, dry_run=dry_run)
        report["tags"].append({"name": tname, "ok": res.get("success")})
    for v in params.get("variables", []) or []:
        res = run_tool("n8n_variable_create", {"body": v}, client=client, dry_run=dry_run)
        report["variables"].append({"key": v.get("key"), "ok": res.get("success")})

    r.step("provision", **{k: len(v) for k, v in report.items() if isinstance(v, list)})
    if any(not x["ok"] for x in report["users"]):
        r.warn("Some user additions need confirmation tokens (production-impact).")
    return r.finish(**report)
