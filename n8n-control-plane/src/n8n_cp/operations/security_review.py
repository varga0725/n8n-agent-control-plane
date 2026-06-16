"""Operation: security_review (spec 5.9) — audit + access + secrets-hygiene +
remediation roadmap."""
from __future__ import annotations

from ..tools import run_tool
from ._util import OpResult, unwrap
from ._instance_common import safe_list, audit_summary, looks_secret


def _roadmap(findings: dict) -> list[str]:
    roadmap = []
    if findings.get("suspiciousVariables"):
        roadmap.append("Migrate secret-like variables into credentials/secret manager.")
    users = findings.get("users", {})
    if isinstance(users, dict) and users.get("pending"):
        roadmap.append(f"Review {users['pending']} pending user invite(s).")
    if findings.get("communityPackages"):
        roadmap.append("Review installed community packages for trust/maintenance.")
    if not roadmap:
        roadmap.append("No high-priority security actions detected from API surface.")
    return roadmap


def security_review(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("security_review")
    findings = {}

    audit = run_tool("n8n_audit_generate", client=client)
    if audit.get("success"):
        findings["audit"] = audit_summary(unwrap(audit))
        r.step("audit", ok=True)
    else:
        r.warn("Security audit endpoint unavailable.")

    users, _ = safe_list(client, "n8n_user_list", {"limit": 250})
    if users is not None:
        owners = [u for u in users if "owner" in str(u.get("role", "")).lower()]
        pending = [u for u in users if u.get("isPending")]
        findings["users"] = {"total": len(users), "owners": len(owners), "pending": len(pending)}
        if len(owners) > 2:
            r.warn(f"{len(owners)} owner-level users — review whether all are needed.")

    variables, _ = safe_list(client, "n8n_variable_list", {"limit": 250})
    if variables is not None:
        suspicious = [v.get("key") for v in variables if looks_secret(str(v.get("value", "")))]
        findings["suspiciousVariables"] = suspicious
        if suspicious:
            r.warn(f"{len(suspicious)} variable(s) look like secrets — move to credentials.")

    pkgs, _ = safe_list(client, "n8n_community_package_list")
    if pkgs is not None:
        findings["communityPackages"] = [p.get("packageName") or p.get("name") for p in pkgs]

    findings["roadmap"] = _roadmap(findings)
    r.step("compile", areas=list(findings.keys()))
    return r.finish(**findings)
