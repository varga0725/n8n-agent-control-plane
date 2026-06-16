"""Operation: execution_triage (spec 5.2) — group failures by workflow/node/
root-cause and prioritize."""
from __future__ import annotations

from collections import Counter

from ..tools import run_tool
from ._util import OpResult, unwrap

_TRANSIENT = ("timeout", "econnreset", "socket hang up", "429", "502", "503",
              "504", "rate limit", "temporarily")
_CRED = ("credential", "unauthorized", "401", "403", "forbidden", "auth")
_EXPR = ("expression", "is not defined", "cannot read properties", "undefined")
_SCHEMA = ("schema", "invalid json", "validation", "required property", "400")


def classify_error(message: str) -> str:
    m = (message or "").lower()
    if any(h in m for h in _CRED):
        return "credential_error"
    if any(h in m for h in _EXPR):
        return "expression_error"
    if any(h in m for h in _SCHEMA):
        return "schema_or_input_error"
    if any(h in m for h in _TRANSIENT):
        return "transient_error"
    return "other"


def error_message(ex: dict) -> str:
    data = ex.get("data", ex) if isinstance(ex, dict) else {}
    node = data
    for key in ("data", "resultData", "error", "message"):
        node = node.get(key) if isinstance(node, dict) else None
        if node is None:
            break
    if isinstance(node, str):
        return node
    return str(data.get("status") or "unknown error")


def execution_triage(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("execution_triage")
    q = {"status": "error", "limit": params.get("limit", 100)}
    for k in ("workflowId", "startedAfter", "startedBefore"):
        if params.get(k):
            q[k] = params[k]
    env = run_tool("n8n_execution_list", q, client=client)
    if not env.get("success"):
        return r.fail("list_failed", "Could not list executions.", detail=env.get("error")).finish()
    execs = unwrap(env)
    execs = execs.get("data", []) if isinstance(execs, dict) else (execs or [])
    r.step("collect", failedCount=len(execs))

    by_workflow, by_cause, details = Counter(), Counter(), []
    for ex in execs:
        msg = error_message(ex)
        cause = classify_error(msg)
        by_workflow[ex.get("workflowId")] += 1
        by_cause[cause] += 1
        details.append({"executionId": ex.get("id"), "workflowId": ex.get("workflowId"),
                        "cause": cause, "message": msg[:200]})

    transient = by_cause.get("transient_error", 0)
    priorities = [{"workflowId": w, "failures": c,
                   "priority": "high" if c >= 5 else "medium" if c >= 2 else "low"}
                  for w, c in by_workflow.most_common()]
    r.step("classify", byCause=dict(by_cause), byWorkflow=dict(by_workflow.most_common(10)))
    return r.finish(failedCount=len(execs), transient=transient,
                    persistent=len(execs) - transient, byCause=dict(by_cause),
                    topWorkflows=by_workflow.most_common(10), priorities=priorities,
                    executions=details[:200])
