"""Deprecated module — operations are now one-file-per-operation (spec section 3).

Kept only as a backward-compatible re-export shim; import from the dedicated
modules instead (e.g. ``from n8n_cp.operations.safe_workflow_deploy import ...``).
"""
from .safe_workflow_deploy import safe_workflow_deploy  # noqa: F401
from .workflow_backup import workflow_backup  # noqa: F401
from .workflow_restore import workflow_restore  # noqa: F401
from .workflow_clone import workflow_clone  # noqa: F401
