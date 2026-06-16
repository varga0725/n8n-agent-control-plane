"""n8n Agent Control Plane — a safe, modular, auditable client for the n8n
Public REST API (v1).

Design goals (see docs/ and the project specification):
  * Capability-first: ask the instance what it supports before acting.
  * Safe by default: read-only, dry-run where possible, destructive blocked
    unless explicitly allowed and confirmed.
  * Typed + validated: every tool is a fixed, named endpoint (no free-form
    method+path), validated before it runs.
  * Auditable: every write produces a structured audit record with secrets
    redacted.

The public surface most callers need:
  * ``Config`` / ``load_config``       — configuration from the environment
  * ``N8nClient``                       — the safe HTTP client
  * ``run_tool``                        — execute a named primitive tool
  * ``REGISTRY``                        — the endpoint/tool registry
"""

from .core.config import Config, load_config
from .core.client import N8nClient
from .core.risk import RiskLevel
from .endpoints import REGISTRY
from .tools import run_tool

__all__ = [
    "Config",
    "load_config",
    "N8nClient",
    "RiskLevel",
    "REGISTRY",
    "run_tool",
]

__version__ = "1.0.0"
