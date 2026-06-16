"""Risk classification.

Every tool/operation is tagged with one of four levels. The level decides what
gating applies before execution:

  read_only          -> runs automatically
  reversible_write   -> runs after validation + audit
  production_impact  -> requires explicit confirmation AND allow_production_writes
  destructive        -> requires explicit confirmation AND allow_destructive

This is the single source of truth used by the client and by policies/.
"""
from __future__ import annotations

from enum import Enum


class RiskLevel(str, Enum):
    READ_ONLY = "read_only"
    REVERSIBLE_WRITE = "reversible_write"
    PRODUCTION_IMPACT = "production_impact"
    DESTRUCTIVE = "destructive"

    @property
    def requires_confirmation(self) -> bool:
        return self in (RiskLevel.PRODUCTION_IMPACT, RiskLevel.DESTRUCTIVE)

    @property
    def rank(self) -> int:
        order = {
            RiskLevel.READ_ONLY: 0,
            RiskLevel.REVERSIBLE_WRITE: 1,
            RiskLevel.PRODUCTION_IMPACT: 2,
            RiskLevel.DESTRUCTIVE: 3,
        }
        return order[self]


def gate_reason(level: RiskLevel, allow_destructive: bool,
                allow_production_writes: bool, confirmed: bool) -> str | None:
    """Return None if the operation may proceed, else a human-readable reason
    why it is blocked. Pure function — easy to unit test."""
    if level == RiskLevel.READ_ONLY:
        return None
    if level == RiskLevel.REVERSIBLE_WRITE:
        return None
    if level == RiskLevel.PRODUCTION_IMPACT:
        if not allow_production_writes:
            return ("Production-impact operation blocked: set "
                    "N8N_ALLOW_PRODUCTION_WRITES=true to enable.")
        if not confirmed:
            return "Production-impact operation requires an explicit confirmation token."
        return None
    if level == RiskLevel.DESTRUCTIVE:
        if not allow_destructive:
            return ("Destructive operation blocked: set "
                    "N8N_ALLOW_DESTRUCTIVE=true to enable.")
        if not confirmed:
            return "Destructive operation requires an explicit confirmation token."
        return None
    return f"Unknown risk level: {level}"
