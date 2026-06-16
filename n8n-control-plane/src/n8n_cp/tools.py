"""Primitive tool dispatcher.

``run_tool(name, params)`` is the one entry point an agent uses for a single API
operation. It:

  1. looks up the fixed :class:`ToolSpec` (no free-form path is possible),
  2. checks the capability registry (don't call unsupported/disabled features),
  3. fills the path template from params and splits out query vs. body,
  4. runs named pre-checks (validation, impact preview, risk escalation),
  5. delegates to ``N8nClient.execute`` for risk gating, confirmation, audit and
     the standard response envelope.

``params`` is a flat dict. Path params (``id``, ``projectId`` …) come from it;
recognized query keys are routed to the query string; everything else under a
``body`` key (or the remaining keys for write tools) becomes the JSON body.
"""
from __future__ import annotations

from typing import Any, Optional

from .core.client import N8nClient
from .core.risk import RiskLevel
from .core import validation, idempotency
from .core.capabilities import fetch_capabilities, Capabilities
from .endpoints import REGISTRY, ToolSpec

# Query params we recognize on list/read endpoints (everything else -> body).
QUERY_KEYS = {
    "limit", "cursor", "offset", "active", "tags", "name", "projectId",
    "workflowId", "status", "includeData", "excludePinnedData",
    "startedAfter", "startedBefore", "lastId", "filter", "sortBy",
    "credentialTypeName",
}


class ToolError(Exception):
    def __init__(self, type_: str, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.type = type_
        self.message = message
        self.details = details or {}


def run_tool(name: str, params: Optional[dict] = None, *,
             client: Optional[N8nClient] = None,
             capabilities: Optional[Capabilities] = None,
             dry_run: bool = False, confirm_token: Optional[str] = None,
             force: bool = False) -> dict:
    params = dict(params or {})
    spec = REGISTRY.get(name)
    if spec is None:
        return _err_envelope(name, "unknown_tool",
                             f"No such tool '{name}'. See REGISTRY for the full list.")

    client = client or N8nClient()

    # 1. capability gate (unless forced) ----------------------------------
    if not force:
        caps = capabilities or fetch_capabilities(client)
        if not caps.is_available(spec.domain):
            return _err_envelope(name, "capability_unavailable",
                                 caps.reason_unavailable(spec.domain) or
                                 f"Domain '{spec.domain}' unavailable.",
                                 risk=spec.risk)
        if spec.beta and spec.domain not in caps.available_domains:
            return _err_envelope(name, "beta_disabled",
                                 f"Beta feature '{spec.domain}' is not enabled on "
                                 f"this instance (requires the relevant feature flag).",
                                 risk=spec.risk)

    # 2. fill path + split query/body -------------------------------------
    try:
        path = _fill_path(spec, params)
    except ToolError as e:
        return _err_envelope(name, e.type, e.message, risk=spec.risk)

    query, body = _split_query_body(spec, params)
    risk = spec.risk
    warnings: list[str] = []
    impact: dict = {}

    # 3. pre-checks --------------------------------------------------------
    try:
        risk, warnings, impact, body, query = _run_pre_checks(
            spec, client, params, body, query, risk, warnings, impact)
    except validation.ValidationError as e:
        return _err_envelope(name, "validation_error", str(e), risk=risk)
    except ToolError as e:
        return _err_envelope(name, e.type, e.message, risk=risk, details=e.details)

    # 4. execute safely ----------------------------------------------------
    resource_id = params.get(spec.resource_id_param) if spec.resource_id_param else None
    return client.execute(
        operation=name, method=spec.method, path=path, risk=risk,
        resource_type=spec.resource_type, resource_id=_as_str(resource_id),
        query=query or None, body=body if spec.body_required or body else None,
        dry_run=dry_run, confirm_token=confirm_token,
        warnings=warnings, impact=impact)


# --------------------------------------------------------------------------
# path / param helpers
# --------------------------------------------------------------------------
def _fill_path(spec: ToolSpec, params: dict) -> str:
    path = spec.path
    for p in spec.path_params:
        if params.get(p) in (None, ""):
            raise ToolError("missing_path_param",
                            f"Tool '{spec.name}' requires path parameter '{p}'.")
        path = path.replace("{" + p + "}", _as_str(params[p]))
    return path


def _split_query_body(spec: ToolSpec, params: dict) -> tuple[dict, Any]:
    # explicit body wins
    if "body" in params and isinstance(params["body"], (dict, list)):
        body = params["body"]
        query = {k: v for k, v in params.items()
                 if k in QUERY_KEYS and k not in spec.path_params}
        return query, body

    query: dict = {}
    body_fields: dict = {}
    for k, v in params.items():
        if k in spec.path_params or k in ("body",):
            continue
        if spec.method == "GET" or k in QUERY_KEYS:
            if k in QUERY_KEYS:
                query[k] = v
        else:
            body_fields[k] = v
    body = body_fields if (spec.body_required and body_fields) else (body_fields or None)
    return query, body


def _as_str(v: Any) -> Optional[str]:
    return None if v is None else str(v)


# --------------------------------------------------------------------------
# pre-check hooks
# --------------------------------------------------------------------------
def _run_pre_checks(spec, client, params, body, query, risk, warnings, impact):
    for check in spec.pre_checks:
        fn = _PRE_CHECKS.get(check)
        if fn:
            risk, warnings, impact, body, query = fn(
                spec, client, params, body, query, risk, warnings, impact)
    return risk, warnings, impact, body, query


def _pc_validate_workflow_body(spec, client, params, body, query, risk, warnings, impact):
    problems = validation.validate_workflow_body(body or {})
    if problems:
        raise validation.ValidationError("; ".join(problems))
    return risk, warnings, impact, body, query


def _pc_force_inactive_create(spec, client, params, body, query, risk, warnings, impact):
    if isinstance(body, dict) and body.get("active"):
        body = dict(body)
        body.pop("active", None)
        warnings.append("Stripped 'active' from create body — workflows are created "
                        "inactive; activate explicitly afterwards.")
    return risk, warnings, impact, body, query


def _pc_dynamic_active_risk(spec, client, params, body, query, risk, warnings, impact):
    """Escalate update risk to production-impact if the live workflow is active."""
    wid = params.get("id")
    try:
        current = client.get(f"/workflows/{wid}")
        cur = current.get("data", current) if isinstance(current, dict) else {}
        if cur.get("active"):
            risk = RiskLevel.PRODUCTION_IMPACT
            impact["currentlyActive"] = True
            warnings.append("Target workflow is ACTIVE — update is production-impact "
                            "and requires confirmation. Prefer n8n_safe_workflow_deploy.")
        else:
            impact["currentlyActive"] = False
    except Exception:
        warnings.append("Could not read current workflow state; treating update "
                        "conservatively as production-impact.")
        risk = RiskLevel.PRODUCTION_IMPACT
    return risk, warnings, impact, body, query


def _pc_require_backup(spec, client, params, body, query, risk, warnings, impact):
    impact["recommendation"] = ("Take a backup with n8n_workflow_backup (or the "
                                "operations layer) before deleting.")
    warnings.append("Destructive: ensure a backup/export exists before deleting.")
    return risk, warnings, impact, body, query


def _pc_default_execution_window(spec, client, params, body, query, risk, warnings, impact):
    if not any(query.get(k) for k in ("workflowId", "status", "startedAfter")):
        query.setdefault("limit", 20)
        warnings.append("No filter given — defaulting to limit=20. Pass workflowId/"
                        "status/startedAfter to target; full history is never auto-pulled.")
    return risk, warnings, impact, body, query


def _pc_idempotency_check(spec, client, params, body, query, risk, warnings, impact):
    eid = params.get("id")
    try:
        ex = client.get(f"/executions/{eid}", query={"includeData": "true"})
        safe, reasons = idempotency.execution_is_retry_safe(
            ex.get("data", ex) if isinstance(ex, dict) else {})
        impact["idempotency"] = {"retrySafe": safe, "reasons": reasons}
        if not safe:
            raise ToolError("retry_unsafe",
                            "Automatic retry blocked: " + " ".join(reasons),
                            {"idempotency": impact["idempotency"]})
        warnings.append("Idempotency heuristic passed, but verify side effects before retry.")
    except ToolError:
        raise
    except Exception:
        raise ToolError("retry_unsafe",
                        "Could not verify execution idempotency — refusing auto-retry. "
                        "Inspect the execution and retry manually if safe.")
    return risk, warnings, impact, body, query


def _pc_bulk_stop_preview(spec, client, params, body, query, risk, warnings, impact):
    ids = (body or {}).get("ids") or (body or {}).get("executionIds") or []
    impact["executionsToStop"] = len(ids)
    warnings.append(f"Bulk stop affects {len(ids)} execution(s).")
    return risk, warnings, impact, body, query


def _pc_credential_usage_check(spec, client, params, body, query, risk, warnings, impact):
    warnings.append("Before deleting, confirm no active workflow references this "
                    "credential (use n8n_credential_validation).")
    impact["recommendation"] = "Run credential usage scan first."
    return risk, warnings, impact, body, query


def _pc_tag_dup_check(spec, client, params, body, query, risk, warnings, impact):
    name = (body or {}).get("name")
    try:
        existing, _, _ = client.paginate("/tags")
        dup = [t for t in existing if (t.get("name") or "").lower() == str(name).lower()]
        if dup:
            warnings.append(f"A tag named '{name}' already exists (id={dup[0].get('id')}). "
                            "Creating a duplicate.")
            impact["duplicateOf"] = dup[0].get("id")
    except Exception:
        pass
    return risk, warnings, impact, body, query


def _pc_require_dry_run_first(spec, client, params, body, query, risk, warnings, impact):
    impact["note"] = ("Source-control pull is production-impact. Run with dry_run "
                      "first to preview changed resources; conflicts/deletions never "
                      "auto-continue.")
    return risk, warnings, impact, body, query


def _pc_warn_secret_in_variable(spec, client, params, body, query, risk, warnings, impact):
    val = str((body or {}).get("value", ""))
    if len(val) > 16 and any(c.isdigit() for c in val) and any(c.isalpha() for c in val):
        warnings.append("Value looks secret-like. Store secrets in credentials or a "
                        "secret manager, not plain variables.")
    return risk, warnings, impact, body, query


def _pc_project_inventory_check(spec, client, params, body, query, risk, warnings, impact):
    pid = params.get("projectId")
    inv = {}
    try:
        wfs, _, _ = client.paginate("/workflows", query={"projectId": pid})
        inv["workflows"] = len(wfs)
    except Exception:
        inv["workflows"] = "unknown"
    impact["projectInventory"] = inv
    if isinstance(inv.get("workflows"), int) and inv["workflows"] > 0:
        warnings.append(f"Project is NOT empty ({inv['workflows']} workflow(s)). "
                        "Non-empty project deletion requires explicit confirmation.")
    return risk, warnings, impact, body, query


def _pc_email_dup_check(spec, client, params, body, query, risk, warnings, impact):
    emails = _emails_from_body(body)
    try:
        users, _, _ = client.paginate("/users")
        existing = {(u.get("email") or "").lower() for u in users}
        dups = [e for e in emails if e.lower() in existing]
        if dups:
            warnings.append("These emails already exist: " + ", ".join(dups))
            impact["duplicateEmails"] = dups
    except Exception:
        pass
    return risk, warnings, impact, body, query


def _pc_owner_role_guard(spec, client, params, body, query, risk, warnings, impact):
    role = str((body or {}).get("newRoleName") or (body or {}).get("role") or "").lower()
    if "owner" in role:
        warnings.append("Assigning/!changing OWNER role is especially high risk.")
        impact["ownerRoleChange"] = True
    return risk, warnings, impact, body, query


def _pc_owner_delete_guard(spec, client, params, body, query, risk, warnings, impact):
    uid = params.get("id")
    try:
        u = client.get(f"/users/{uid}")
        ud = u.get("data", u) if isinstance(u, dict) else {}
        if "owner" in str(ud.get("role", "")).lower() or ud.get("isOwner"):
            warnings.append("This user appears to be an OWNER — deletion is extremely "
                            "high risk and may orphan resources.")
            impact["deletingOwner"] = True
    except Exception:
        pass
    return risk, warnings, impact, body, query


def _pc_folder_contents_check(spec, client, params, body, query, risk, warnings, impact):
    warnings.append("Check the folder's contents before deletion; move or delete "
                    "child resources first.")
    return risk, warnings, impact, body, query


def _pc_require_update_filter(spec, client, params, body, query, risk, warnings, impact):
    if not isinstance(body, dict) or not body.get("filter"):
        raise validation.ValidationError(
            "Row update requires an explicit 'filter' to avoid updating every row.")
    return risk, warnings, impact, body, query


def _pc_reject_empty_delete_filter(spec, client, params, body, query, risk, warnings, impact):
    validation.reject_empty_delete_filter(body)
    return risk, warnings, impact, body, query


def _pc_row_delete_preview(spec, client, params, body, query, risk, warnings, impact):
    dtid = params.get("dataTableId")
    try:
        res = client.get(f"/data-tables/{dtid}/rows",
                         query={"filter": (body or {}).get("filter"), "limit": 1})
        count = res.get("count")
        impact["rowsMatchingFilter"] = count
        if count is not None:
            warnings.append(f"About {count} row(s) match the delete filter.")
    except Exception:
        warnings.append("Could not preview row count; proceed with caution.")
    return risk, warnings, impact, body, query


def _pc_column_delete_warning(spec, client, params, body, query, risk, warnings, impact):
    warnings.append("Deleting a column permanently removes its data from every row.")
    impact["dataLoss"] = True
    return risk, warnings, impact, body, query


def _pc_validate_package_ref(spec, client, params, body, query, risk, warnings, impact):
    name = (body or {}).get("name")
    if not name:
        raise validation.ValidationError("Package install requires a package 'name'.")
    impact["package"] = name
    warnings.append("Production auto-install is discouraged; review the package and "
                    "affected workflows first.")
    return risk, warnings, impact, body, query


def _pc_package_usage_check(spec, client, params, body, query, risk, warnings, impact):
    warnings.append("Before uninstalling, find workflows using this package's nodes; "
                    "they will break.")
    return risk, warnings, impact, body, query


def _pc_validate_import_plan(spec, client, params, body, query, risk, warnings, impact):
    impact["note"] = ("Validate the package, check workflow/credential conflicts and "
                      "the target project before import. Beta feature.")
    return risk, warnings, impact, body, query


def _emails_from_body(body) -> list[str]:
    if isinstance(body, dict):
        if isinstance(body.get("email"), str):
            return [body["email"]]
        if isinstance(body.get("users"), list):
            return [u.get("email") for u in body["users"] if u.get("email")]
    if isinstance(body, list):
        return [u.get("email") for u in body if isinstance(u, dict) and u.get("email")]
    return []


_PRE_CHECKS = {
    "validate_workflow_body": _pc_validate_workflow_body,
    "force_inactive_create": _pc_force_inactive_create,
    "dynamic_active_risk": _pc_dynamic_active_risk,
    "require_backup": _pc_require_backup,
    "default_execution_window": _pc_default_execution_window,
    "idempotency_check": _pc_idempotency_check,
    "bulk_stop_preview": _pc_bulk_stop_preview,
    "credential_usage_check": _pc_credential_usage_check,
    "tag_dup_check": _pc_tag_dup_check,
    "require_dry_run_first": _pc_require_dry_run_first,
    "warn_secret_in_variable": _pc_warn_secret_in_variable,
    "project_inventory_check": _pc_project_inventory_check,
    "email_dup_check": _pc_email_dup_check,
    "owner_role_guard": _pc_owner_role_guard,
    "owner_delete_guard": _pc_owner_delete_guard,
    "folder_contents_check": _pc_folder_contents_check,
    "require_update_filter": _pc_require_update_filter,
    "reject_empty_delete_filter": _pc_reject_empty_delete_filter,
    "row_delete_preview": _pc_row_delete_preview,
    "column_delete_warning": _pc_column_delete_warning,
    "validate_package_ref": _pc_validate_package_ref,
    "package_usage_check": _pc_package_usage_check,
    "validate_import_plan": _pc_validate_import_plan,
}


def _err_envelope(operation: str, type_: str, message: str, *,
                  risk: RiskLevel = RiskLevel.READ_ONLY,
                  details: Optional[dict] = None) -> dict:
    from .core.errors import new_audit_id
    return {
        "success": False,
        "operation": operation,
        "riskLevel": risk.value,
        "error": {"type": type_, "message": message, "statusCode": None,
                  "retryable": False, "details": details or {}},
        "auditId": new_audit_id(),
        "durationMs": 0,
    }
