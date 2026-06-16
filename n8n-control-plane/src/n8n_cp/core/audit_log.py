"""Spec-name alias for the audit logger (spec section 3 lists `audit-log`).

The implementation lives in ``audit.py``; this re-export keeps the spec's file
name available without duplicating code.
"""
from .audit import AuditLogger  # noqa: F401
