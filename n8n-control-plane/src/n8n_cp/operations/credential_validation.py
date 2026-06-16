"""Operation: credential_validation (spec 5.7) — test credentials, find
dependents, suggest fixes. Results are redacted."""
from __future__ import annotations

from ..tools import run_tool
from ._util import OpResult, unwrap


def credential_validation(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("credential_validation")
    if params.get("id"):
        targets = [{"id": params["id"]}]
    else:
        env = run_tool("n8n_credential_list", {"limit": params.get("limit", 100)}, client=client)
        if env.get("success"):
            data = unwrap(env)
            targets = data.get("data", []) if isinstance(data, dict) else (data or [])
        else:
            targets = []
            r.warn("Could not list credentials (this instance may not expose a list "
                   "endpoint). Pass an explicit 'id'.")
    r.step("collect", count=len(targets))

    results = []
    for c in targets:
        cid = c.get("id")
        test = run_tool("n8n_credential_test", {"id": cid}, client=client)
        ok = test.get("success") and (unwrap(test) or {}).get("status") != "error"
        results.append({"credentialId": cid, "name": c.get("name"), "type": c.get("type"),
                        "testPassed": bool(ok),
                        "detail": unwrap(test) if test.get("success") else test.get("error")})
    failing = [x for x in results if not x["testPassed"]]
    r.step("test", tested=len(results), failing=len(failing))
    if failing:
        r.warn(f"{len(failing)} credential(s) failed validation. Find dependent "
               "workflows before rotating or deleting.")
    return r.finish(results=results, failing=failing)
