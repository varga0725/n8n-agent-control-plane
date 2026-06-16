import os
import re

from n8n_cp.endpoints import REGISTRY, _SPECS
from n8n_cp.core.risk import RiskLevel

POLICY = os.path.join(os.path.dirname(__file__), "..", "..", "policies", "permissions.yaml")


def test_every_tool_has_consistent_name_and_path():
    for spec in _SPECS:
        assert spec.name.startswith("n8n_"), spec.name
        # path placeholders must all be declared as path_params
        placeholders = set(re.findall(r"{(\w+)}", spec.path))
        assert placeholders == set(spec.path_params), spec.name
        assert spec.method in ("GET", "POST", "PUT", "PATCH", "DELETE")


def test_registry_is_unique():
    names = [s.name for s in _SPECS]
    assert len(names) == len(set(names))


def test_destructive_tools_are_marked():
    # A DELETE that isn't a "test"/read must be destructive or production-impact.
    for s in _SPECS:
        if s.method == "DELETE":
            assert s.risk in (RiskLevel.DESTRUCTIVE,), s.name


def test_policy_yaml_matches_registry_risk():
    risks = _parse_policy_tools(POLICY)
    # Every tool in the registry appears in the policy with the same risk.
    for name, spec in REGISTRY.items():
        assert name in risks, f"{name} missing from permissions.yaml"
        assert risks[name] == spec.risk.value, (
            f"{name}: policy={risks[name]} vs code={spec.risk.value}")


def _parse_policy_tools(path):
    """Minimal YAML scan for the `tools:` block (no pyyaml dependency)."""
    risks = {}
    in_tools = False
    with open(path) as f:
        for line in f:
            if line.startswith("tools:"):
                in_tools = True
                continue
            if in_tools:
                if line and not line.startswith((" ", "\t")) and line.strip():
                    break  # left the block
                m = re.match(r"\s+([A-Za-z0-9_]+):\s*([a-z_]+)", line)
                if m:
                    risks[m.group(1)] = m.group(2)
    return risks
