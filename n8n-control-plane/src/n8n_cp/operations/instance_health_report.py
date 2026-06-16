"""Operation: instance_health_report (spec 5.8) — aggregate a full instance
health picture."""
from __future__ import annotations

from ..core.capabilities import fetch_capabilities
from ..tools import run_tool
from ._util import OpResult, unwrap
from ._instance_common import safe_list, audit_summary


def _maintenance_suggestions(report: dict) -> list[str]:
    s = []
    wf = report.get("workflows", {})
    if isinstance(wf, dict):
        if wf.get("archived", 0) > 0:
            s.append(f"{wf['archived']} archived workflow(s) — consider deleting after export.")
        if wf.get("inactive", 0) > wf.get("active", 0):
            s.append("More inactive than active workflows — audit for abandoned flows.")
    if report.get("recentErrorRate", 0) > 0.1:
        s.append("Recent error rate >10% — run execution_triage.")
    if report.get("failedExecutions", 0) > 0:
        s.append("Failed executions present — run failed_execution_recovery.")
    return s


def instance_health_report(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("instance_health_report")
    caps = fetch_capabilities(client)
    r.step("discover", domains=sorted(caps.available_domains))
    report = {"capabilities": sorted(caps.available_domains)}

    wfs, _ = safe_list(client, "n8n_workflow_list", {"limit": 250})
    if wfs is not None:
        active = [w for w in wfs if w.get("active")]
        archived = [w for w in wfs if w.get("isArchived") or w.get("archived")]
        report["workflows"] = {"total": len(wfs), "active": len(active),
                               "inactive": len(wfs) - len(active), "archived": len(archived)}
    else:
        r.warn("Workflow listing unavailable.")

    fails, _ = safe_list(client, "n8n_execution_list", {"status": "error", "limit": 100})
    if fails is not None:
        report["failedExecutions"] = len(fails)
    runs, _ = safe_list(client, "n8n_execution_list", {"limit": 100})
    if runs:
        errors = sum(1 for e in runs if e.get("status") == "error")
        report["recentErrorRate"] = round(errors / len(runs), 3)
        report["longRunning"] = [e.get("id") for e in runs if e.get("status") == "running"][:10]

    if caps.is_available("insights"):
        ins = run_tool("n8n_insights_summary", client=client)
        if ins.get("success"):
            report["insights"] = unwrap(ins)
    if caps.is_available("community-packages"):
        pkgs, _ = safe_list(client, "n8n_community_package_list")
        if pkgs is not None:
            report["communityPackages"] = len(pkgs)
    if caps.is_available("audit"):
        audit = run_tool("n8n_audit_generate", client=client)
        if audit.get("success"):
            report["securityAudit"] = audit_summary(unwrap(audit))

    report["recommendedMaintenance"] = _maintenance_suggestions(report)
    r.step("aggregate", keys=list(report.keys()))
    return r.finish(**report)
