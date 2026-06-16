from n8n_cp.core.risk import RiskLevel, gate_reason


def test_read_only_and_reversible_pass_without_flags():
    assert gate_reason(RiskLevel.READ_ONLY, False, False, False) is None
    assert gate_reason(RiskLevel.REVERSIBLE_WRITE, False, False, False) is None


def test_production_impact_needs_flag_and_confirmation():
    assert gate_reason(RiskLevel.PRODUCTION_IMPACT, False, False, False) is not None
    assert gate_reason(RiskLevel.PRODUCTION_IMPACT, False, True, False) is not None  # no confirm
    assert gate_reason(RiskLevel.PRODUCTION_IMPACT, False, True, True) is None


def test_destructive_needs_flag_and_confirmation():
    assert gate_reason(RiskLevel.DESTRUCTIVE, False, False, False) is not None
    assert gate_reason(RiskLevel.DESTRUCTIVE, True, False, False) is not None  # no confirm
    assert gate_reason(RiskLevel.DESTRUCTIVE, True, False, True) is None


def test_rank_ordering():
    assert RiskLevel.READ_ONLY.rank < RiskLevel.DESTRUCTIVE.rank
