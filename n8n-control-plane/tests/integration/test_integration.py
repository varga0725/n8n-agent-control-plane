"""Integration tests against a DISPOSABLE n8n instance.

Env-gated so they never run by accident. Requires:
    N8N_RUN_INTEGRATION=1
    N8N_BASE_URL, N8N_API_KEY  (pointing at a TEST instance)
    N8N_ALLOW_DESTRUCTIVE=1 N8N_ALLOW_PRODUCTION_WRITES=1
"""
import json
import os

import pytest

from n8n_cp.core.client import N8nClient
from n8n_cp.tools import run_tool
from n8n_cp.operations import safe_workflow_deploy

pytestmark = pytest.mark.skipif(
    os.environ.get("N8N_RUN_INTEGRATION") != "1",
    reason="set N8N_RUN_INTEGRATION=1 (against a disposable instance) to run")

FIXTURE = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_workflow.json")


@pytest.fixture(scope="module")
def client():
    return N8nClient()


def _confirm(c, name, params):
    """Helper: do the blocked->token->confirm dance for gated tools."""
    first = run_tool(name, params, client=c)
    if first.get("success"):
        return first
    token = first["error"]["details"].get("confirmationToken")
    return run_tool(name, params, client=c, confirm_token=token)


def test_workflow_lifecycle(client):
    body = json.load(open(FIXTURE))
    created = run_tool("n8n_workflow_create", {"body": body}, client=client)
    assert created["success"], created
    wid = created["data"]["id"]
    try:
        assert run_tool("n8n_workflow_get", {"id": wid}, client=client)["success"]
        # update via the safe operation
        body["name"] = body["name"] + " (edited)"
        dep = safe_workflow_deploy(client, {"id": wid, "workflow": body})
        assert dep["success"], dep
        # activate (production-impact) then deactivate
        act = _confirm(client, "n8n_workflow_activate", {"id": wid})
        assert act["success"], act
        _confirm(client, "n8n_workflow_deactivate", {"id": wid})
        # archive / unarchive
        run_tool("n8n_workflow_archive", {"id": wid}, client=client)
        run_tool("n8n_workflow_unarchive", {"id": wid}, client=client)
    finally:
        deleted = _confirm(client, "n8n_workflow_delete", {"id": wid})
        assert deleted["success"], deleted


def test_credential_schema_read(client):
    r = run_tool("n8n_credential_get_schema",
                 {"credentialTypeName": "httpHeaderAuth"}, client=client)
    assert r["success"]
