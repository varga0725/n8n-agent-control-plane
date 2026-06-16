"""Production-safe smoke tests — READ ONLY. Env-gated.

Requires N8N_RUN_SMOKE=1 plus N8N_BASE_URL/N8N_API_KEY. Only read-only calls, so
safe against production.
"""
import os

import pytest

from n8n_cp.core.client import N8nClient
from n8n_cp.tools import run_tool

pytestmark = pytest.mark.skipif(
    os.environ.get("N8N_RUN_SMOKE") != "1",
    reason="set N8N_RUN_SMOKE=1 to run read-only smoke tests")


@pytest.fixture(scope="module")
def client():
    return N8nClient()


def test_discover(client):
    assert run_tool("n8n_discover_capabilities", client=client)["success"]


@pytest.mark.parametrize("tool", [
    "n8n_workflow_list", "n8n_execution_list", "n8n_project_list",
    "n8n_credential_list",
])
def test_read_only_list(client, tool):
    r = run_tool(tool, {"limit": 1}, client=client)
    # Some lists may be unavailable on a given edition; accept success or a clean
    # capability error, but never a crash.
    assert "success" in r


def test_insights_summary(client):
    r = run_tool("n8n_insights_summary", client=client)
    assert "success" in r
