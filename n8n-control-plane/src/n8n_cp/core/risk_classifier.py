"""Spec-name alias for risk classification (spec section 3 lists `risk-classifier`).

The implementation lives in ``risk.py``; this re-export keeps the spec's file
name available without duplicating code.
"""
from .risk import RiskLevel, gate_reason  # noqa: F401
