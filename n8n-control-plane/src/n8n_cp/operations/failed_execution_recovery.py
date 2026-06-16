"""Operation: failed_execution_recovery (spec 5.3) — classify failures, retry
only the idempotent-safe ones (payments/emails/etc. excluded), with confirmation."""
from __future__ import annotations

from ..core import idempotency
from ..tools import run_tool
from ._util import OpResult, unwrap
from .execution_triage import classify_error, error_message


def failed_execution_recovery(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("failed_execution_recovery")
    ids = params.get("executionIds")
    if not ids:
        q = {"status": "error", "limit": params.get("limit", 50)}
        if params.get("workflowId"):
            q["workflowId"] = params["workflowId"]
        env = run_tool("n8n_execution_list", q, client=client)
        items = unwrap(env)
        items = items.get("data", []) if isinstance(items, dict) else items
        ids = [e.get("id") for e in (items or [])]
    r.step("targets", count=len(ids))

    retry_safe, manual, blocked = [], [], []
    for eid in ids:
        ex_env = run_tool("n8n_execution_get", {"id": eid, "includeData": "true"}, client=client)
        ex = unwrap(ex_env)
        safe, reasons = idempotency.execution_is_retry_safe(ex if isinstance(ex, dict) else {})
        cause = classify_error(error_message(ex if isinstance(ex, dict) else {}))
        record = {"executionId": eid, "cause": cause, "reasons": reasons}
        if not safe or cause in ("credential_error", "expression_error", "schema_or_input_error"):
            (manual if cause != "other" else blocked).append(record)
        elif cause == "transient_error" or safe:
            retry_safe.append(record)
        else:
            manual.append(record)
    r.step("classify", retrySafe=len(retry_safe), manual=len(manual), blocked=len(blocked))

    issued = []
    if params.get("auto") and retry_safe:
        for rec in retry_safe:
            res = run_tool("n8n_execution_retry", {"id": rec["executionId"]}, client=client,
                           dry_run=dry_run, confirm_token=confirm_token)
            issued.append({"executionId": rec["executionId"], "success": res.get("success"),
                           "riskLevel": res.get("riskLevel")})
        r.step("retry", issued=len(issued))
    else:
        r.warn("No retries issued. Re-run with auto=true (and a confirmation token) "
               "to retry the retry-safe set; manual-review items are never auto-retried.")
    return r.finish(retrySafe=retry_safe, manualReview=manual, blocked=blocked, issued=issued)
