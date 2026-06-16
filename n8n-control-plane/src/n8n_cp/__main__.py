"""Command-line entry point for the n8n control plane.

Examples
--------
  # configuration + connectivity
  python3 -m n8n_cp doctor
  python3 -m n8n_cp discover

  # list everything the agent can call
  python3 -m n8n_cp tools
  python3 -m n8n_cp tools --domain workflows

  # run a primitive tool (params as JSON or k=v pairs)
  python3 -m n8n_cp run n8n_workflow_list --param limit=5
  python3 -m n8n_cp run n8n_workflow_get --param id=128
  python3 -m n8n_cp run n8n_workflow_delete --param id=128 --dry-run
  python3 -m n8n_cp run n8n_workflow_delete --param id=128 --confirm <TOKEN>

  # run a high-level operation
  python3 -m n8n_cp op instance_health_report
  python3 -m n8n_cp op safe_workflow_deploy --json '{"id":"128","workflow":{...}}'

All output is a single JSON envelope (or JSON array for listings).
"""
from __future__ import annotations

import argparse
import json
import sys

from .core.config import load_config
from .core.client import N8nClient
from .endpoints import REGISTRY, by_domain
from .tools import run_tool
from . import operations


def _parse_params(args) -> dict:
    params: dict = {}
    if args.json:
        params.update(json.loads(args.json))
    for kv in args.param or []:
        if "=" not in kv:
            sys.exit(f"--param must be key=value, got: {kv}")
        k, v = kv.split("=", 1)
        params[k] = _coerce(v)
    return params


def _coerce(v: str):
    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    if v.isdigit():
        return int(v)
    if v.startswith(("{", "[")):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return v
    return v


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="n8n_cp", description="n8n Agent Control Plane")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Validate configuration and connectivity.")
    sub.add_parser("discover", help="Run capability discovery (GET /discover).")

    pt = sub.add_parser("tools", help="List available primitive tools.")
    pt.add_argument("--domain", help="Filter by domain.")

    pr = sub.add_parser("run", help="Run a primitive tool.")
    pr.add_argument("tool")
    pr.add_argument("--param", action="append", help="key=value (repeatable)")
    pr.add_argument("--json", help="params as a JSON object")
    pr.add_argument("--dry-run", action="store_true")
    pr.add_argument("--confirm", help="confirmation token")
    pr.add_argument("--force", action="store_true", help="skip capability gate")

    po = sub.add_parser("op", help="Run a high-level operation.")
    po.add_argument("operation")
    po.add_argument("--param", action="append")
    po.add_argument("--json")
    po.add_argument("--dry-run", action="store_true")
    po.add_argument("--confirm")

    a = p.parse_args(argv)

    if a.cmd == "doctor":
        cfg = load_config()
        problems = cfg.validate()
        out = {"config": cfg.safe_dict(), "problems": problems,
               "ok": not any("not set" in x for x in problems)}
        _print(out)
        return 0

    if a.cmd == "discover":
        _print(run_tool("n8n_discover_capabilities"))
        return 0

    if a.cmd == "tools":
        groups = by_domain()
        out = {}
        for domain, specs in sorted(groups.items()):
            if a.domain and domain != a.domain:
                continue
            out[domain] = [{"name": s.name, "method": s.method, "path": s.path,
                            "risk": s.risk.value, "beta": s.beta,
                            "summary": s.summary} for s in specs]
        _print(out)
        return 0

    if a.cmd == "run":
        params = _parse_params(a)
        env = run_tool(a.tool, params, dry_run=a.dry_run,
                       confirm_token=a.confirm, force=a.force)
        _print(env)
        return 0 if env.get("success") else 1

    if a.cmd == "op":
        params = _parse_params(a)
        fn = operations.get(a.operation)
        if fn is None:
            _print({"success": False, "error": f"Unknown operation '{a.operation}'. "
                    f"Available: {', '.join(operations.available())}"})
            return 1
        client = N8nClient()
        env = fn(client, params, dry_run=a.dry_run, confirm_token=a.confirm)
        _print(env)
        return 0 if env.get("success", True) else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
