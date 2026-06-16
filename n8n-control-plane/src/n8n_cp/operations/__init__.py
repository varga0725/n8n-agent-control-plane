"""High-level operations — multi-step, validated, audited, recoverable flows.

These are the difference between an API wrapper and a control plane. Each takes
``(client, params, *, dry_run=False, confirm_token=None)`` and returns a result
dict with a ``steps`` trace so the human can see exactly what happened.

One file per operation (spec section 3). Operations compose the primitive tools
and core services (diff, backup, idempotency) and never bypass risk gating.
"""
from __future__ import annotations

from typing import Callable

from .safe_workflow_deploy import safe_workflow_deploy
from .workflow_backup import workflow_backup
from .workflow_restore import workflow_restore
from .workflow_clone import workflow_clone
from .workflow_migration import workflow_migration
from .execution_triage import execution_triage
from .failed_execution_recovery import failed_execution_recovery
from .project_bootstrap import project_bootstrap
from .credential_validation import credential_validation
from .instance_health_report import instance_health_report
from .security_review import security_review
from .source_control_sync import source_control_sync
from .disaster_recovery import disaster_recovery

_REGISTRY: dict[str, Callable] = {
    "safe_workflow_deploy": safe_workflow_deploy,
    "workflow_backup": workflow_backup,
    "workflow_restore": workflow_restore,
    "workflow_clone": workflow_clone,
    "workflow_migration": workflow_migration,
    "execution_triage": execution_triage,
    "failed_execution_recovery": failed_execution_recovery,
    "project_bootstrap": project_bootstrap,
    "credential_validation": credential_validation,
    "instance_health_report": instance_health_report,
    "security_review": security_review,
    "source_control_sync": source_control_sync,
    "disaster_recovery": disaster_recovery,
}


def get(name: str):
    return _REGISTRY.get(name)


def available() -> list[str]:
    return sorted(_REGISTRY)


__all__ = ["get", "available", *_REGISTRY.keys()]
