"""Lightweight request validation.

Two jobs:
  1. Ensure required path/body params for a tool are present before any request.
  2. Reject dangerous data-table delete filters (empty / overly broad), per the
     spec's hard rule that a bulk delete with an empty filter must never run.
"""
from __future__ import annotations

from typing import Any


class ValidationError(Exception):
    pass


def require(params: dict, names: list[str], where: str = "params") -> None:
    missing = [n for n in names if params.get(n) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required {where}: {', '.join(missing)}")


def reject_empty_delete_filter(body: Any) -> None:
    """Data Tables row delete: a missing/empty filter would wipe the table."""
    if not isinstance(body, dict):
        raise ValidationError("Row delete requires a body with an explicit filter.")
    flt = body.get("filter")
    if flt in (None, {}, [], ""):
        raise ValidationError(
            "Refusing row delete with an empty/absent filter — this would delete "
            "every row. Provide a specific filter, or use a dedicated truncate "
            "operation with explicit confirmation.")
    # A filter that is present but has no conditions is equally dangerous.
    if isinstance(flt, dict):
        conds = flt.get("conditions") or flt.get("filters")
        if conds is not None and len(conds) == 0:
            raise ValidationError(
                "Row delete filter has no conditions — refusing as too broad.")


def validate_workflow_body(body: Any) -> list[str]:
    """Structural sanity check for a workflow create/update body. Returns a list
    of problems (empty = ok). Mirrors the n8n schema's required fields."""
    problems = []
    if not isinstance(body, dict):
        return ["Workflow body must be an object."]
    for f in ("name", "nodes", "connections", "settings"):
        if f not in body:
            problems.append(f"Workflow body missing required field '{f}'.")
    if isinstance(body.get("nodes"), list):
        names = [n.get("name") for n in body["nodes"]]
        if len(names) != len(set(names)):
            problems.append("Duplicate node names — connections key by name.")
    return problems
