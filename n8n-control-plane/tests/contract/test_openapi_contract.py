"""OpenAPI contract tests (spec 17.2).

Validates the tool registry against the real n8n Public API OpenAPI spec at
``openapi/n8n-openapi.json``. Skips cleanly if the spec file isn't present so the
suite still runs offline without it.
"""
import json
import os
import re

import pytest

from n8n_cp.endpoints import _SPECS

SPEC_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "openapi",
                         "n8n-openapi.json")

pytestmark = pytest.mark.skipif(
    not os.path.exists(SPEC_PATH),
    reason="openapi/n8n-openapi.json not present (place the instance spec there)")


@pytest.fixture(scope="module")
def spec():
    with open(SPEC_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def spec_ops(spec):
    ops = {}
    for path, methods in spec["paths"].items():
        for m, op in methods.items():
            if m.lower() in ("get", "post", "put", "patch", "delete"):
                ops[(m.upper(), path)] = op
    return ops


def test_every_registry_tool_exists_in_spec(spec_ops):
    missing = [(s.method, s.path) for s in _SPECS if (s.method, s.path) not in spec_ops]
    assert not missing, f"Tools not found in OpenAPI spec: {missing}"


def test_no_spec_endpoint_is_unmapped(spec_ops):
    reg = {(s.method, s.path) for s in _SPECS}
    unmapped = [k for k in spec_ops if k not in reg]
    assert not unmapped, f"Spec endpoints with no primitive tool: {unmapped}"


def test_path_params_match_spec(spec_ops):
    problems = []
    for s in _SPECS:
        spec_params = set(re.findall(r"{(\w+)}", s.path))
        if spec_params != set(s.path_params):
            problems.append((s.name, spec_params, set(s.path_params)))
    assert not problems, f"Path param mismatches: {problems}"


def test_body_required_tools_have_request_body(spec_ops):
    # Tools we marked body_required should correspond to spec ops that accept a
    # requestBody (POST/PUT/PATCH). This catches accidental misclassification.
    problems = []
    for s in _SPECS:
        if s.body_required:
            op = spec_ops.get((s.method, s.path), {})
            if "requestBody" not in op and s.method in ("POST", "PUT", "PATCH"):
                problems.append(s.name)
    # Some endpoints legitimately take no body even on POST (e.g. activate); allow
    # a small known set rather than failing the whole suite.
    allowed = set()
    real = [p for p in problems if p not in allowed]
    assert not real, f"body_required tools without a spec requestBody: {real}"
