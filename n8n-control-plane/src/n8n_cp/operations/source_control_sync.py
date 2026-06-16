"""Operation: source_control_sync (spec 5.10) — safe git pull: capability ->
dry-run preview -> confirm -> pull -> report -> post-pull health check."""
from __future__ import annotations

from ..core.capabilities import fetch_capabilities
from ..tools import run_tool
from ._util import OpResult, unwrap
from .instance_health_report import instance_health_report


def source_control_sync(client, params, *, dry_run=False, confirm_token=None) -> dict:
    r = OpResult("source_control_sync")
    caps = fetch_capabilities(client)
    if not caps.is_available("source-control"):
        return r.fail("unavailable", "Source control is not available on this instance.").finish()

    preview = run_tool("n8n_source_control_pull", {"body": {"force": False}},
                       client=client, dry_run=True)
    r.step("preview", changes=unwrap(preview))

    if not confirm_token:
        r.warn("Pull is production-impact. Review the preview, then re-run with a "
               "confirmation token. Conflicts/deletions never auto-continue.")
        return r.finish(preview=unwrap(preview), needsConfirmation=True)

    pull = run_tool("n8n_source_control_pull", {"body": params.get("body", {"force": False})},
                    client=client, dry_run=dry_run, confirm_token=confirm_token)
    r.step("pull", status="ok" if pull.get("success") else "blocked")
    r.data["pull"] = pull
    if pull.get("success"):
        health = instance_health_report(client, {})
        r.step("post_health", ok=health.get("success"))
        r.data["postHealth"] = health.get("data")
    r.success = pull.get("success", False) or dry_run
    return r.finish()
