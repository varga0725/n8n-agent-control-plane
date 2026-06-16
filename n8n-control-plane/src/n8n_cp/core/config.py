"""Configuration loaded from the environment.

Secrets only ever live here, read from environment variables. The API key is
never logged, never serialized into audit records, never echoed in errors, and
never written to disk by this package. See SECURITY.md.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from typing import Optional


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        return default


@dataclass
class Config:
    """Runtime configuration. Construct via :func:`load_config`.

    The three safety switches (``allow_destructive``, ``allow_production_writes``,
    ``redact_secrets``) default to the safe setting. They cannot be flipped by an
    agent prompt — only by the operator's environment.
    """

    base_url: str
    api_key: str = field(repr=False, default="")
    request_timeout_ms: int = 30000
    max_retries: int = 3
    allow_destructive: bool = False
    allow_production_writes: bool = False
    default_project_id: Optional[str] = None
    audit_log_enabled: bool = True
    redact_secrets: bool = True
    redact_execution_data: bool = True
    backup_dir: str = "./backups"
    audit_dir: str = "./audit"

    def validate(self) -> list[str]:
        """Return a list of human-readable configuration problems (empty = ok)."""
        problems: list[str] = []
        if not self.base_url:
            problems.append("N8N_BASE_URL is not set.")
        elif not self.base_url.startswith(("http://", "https://")):
            problems.append("N8N_BASE_URL must start with http:// or https://")
        if self.base_url.rstrip("/").endswith("/api/v1") is False:
            # Not fatal — we normalize — but warn so the operator knows.
            problems.append(
                "N8N_BASE_URL should usually end with /api/v1 "
                "(e.g. https://host/api/v1). It will be normalized."
            )
        if not self.api_key:
            problems.append("N8N_API_KEY is not set — only --dry-run will work.")
        if self.request_timeout_ms < 1000:
            problems.append("N8N_REQUEST_TIMEOUT_MS is suspiciously low (<1000).")
        return problems

    @property
    def api_root(self) -> str:
        """Base URL guaranteed to end in /api/v1 with no trailing slash."""
        b = self.base_url.rstrip("/")
        if b.endswith("/api/v1"):
            return b
        return b + "/api/v1"

    def safe_dict(self) -> dict:
        """Config as a dict with the api_key removed — safe to log."""
        d = asdict(self)
        d.pop("api_key", None)
        return d


def load_config() -> Config:
    return Config(
        base_url=os.environ.get("N8N_BASE_URL", ""),
        api_key=os.environ.get("N8N_API_KEY", ""),
        request_timeout_ms=_int("N8N_REQUEST_TIMEOUT_MS", 30000),
        max_retries=_int("N8N_MAX_RETRIES", 3),
        allow_destructive=_bool("N8N_ALLOW_DESTRUCTIVE", False),
        allow_production_writes=_bool("N8N_ALLOW_PRODUCTION_WRITES", False),
        default_project_id=os.environ.get("N8N_DEFAULT_PROJECT_ID") or None,
        audit_log_enabled=_bool("N8N_AUDIT_LOG_ENABLED", True),
        redact_secrets=_bool("N8N_REDACT_SECRETS", True),
        redact_execution_data=_bool("N8N_REDACT_EXECUTION_DATA", True),
        backup_dir=os.environ.get("N8N_BACKUP_DIR", "./backups"),
        audit_dir=os.environ.get("N8N_AUDIT_DIR", "./audit"),
    )
