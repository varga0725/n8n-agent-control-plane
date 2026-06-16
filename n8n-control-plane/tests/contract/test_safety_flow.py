"""End-to-end safety behavior using the in-memory MockTransport (offline)."""
import os

from n8n_cp.core.client import N8nClient
from n8n_cp.transports.mock import MockTransport
from n8n_cp.core.capabilities import Capabilities
from n8n_cp.tools import run_tool


def _client(transport):
    os.environ["N8N_AUDIT_LOG_ENABLED"] = "false"
    return N8nClient(transport=transport)


def _caps(*domains):
    return Capabilities(available_domains=set(domains))


def test_read_only_runs_without_confirmation():
    mt = MockTransport().stub("GET", "/workflows", 200, {"data": [{"id": "1"}]})
    r = run_tool("n8n_workflow_list", {"limit": 5}, client=_client(mt),
                 capabilities=_caps("workflows"))
    assert r["success"] and r["riskLevel"] == "read_only"


def test_destructive_blocked_then_token_unlocks(monkeypatch):
    monkeypatch.setenv("N8N_ALLOW_DESTRUCTIVE", "true")
    mt = MockTransport().stub("DELETE", "/workflows/9", 200, {"deleted": True})
    c = _client(mt)
    caps = _caps("workflows")
    blocked = run_tool("n8n_workflow_delete", {"id": "9"}, client=c, capabilities=caps)
    assert not blocked["success"]
    token = blocked["error"]["details"]["confirmationToken"]
    ok = run_tool("n8n_workflow_delete", {"id": "9"}, client=c, capabilities=caps,
                  confirm_token=token)
    assert ok["success"]


def test_destructive_blocked_when_flag_off():
    mt = MockTransport().stub("DELETE", "/workflows/9", 200, {})
    r = run_tool("n8n_workflow_delete", {"id": "9"}, client=_client(mt),
                 capabilities=_caps("workflows"))
    assert not r["success"]
    assert r["error"]["type"] in ("policy_blocked", "confirmation_required")


def test_empty_datatable_delete_filter_refused():
    mt = MockTransport()
    r = run_tool("n8n_data_table_row_delete", {"dataTableId": "5", "body": {}},
                 client=_client(mt), capabilities=_caps("data-tables"))
    assert not r["success"] and r["error"]["type"] == "validation_error"


def test_capability_gate_blocks_unavailable_domain():
    mt = MockTransport()
    r = run_tool("n8n_data_table_list", {}, client=_client(mt),
                 capabilities=_caps("workflows"))  # data-tables NOT available
    assert not r["success"] and r["error"]["type"] == "capability_unavailable"


def test_unknown_tool_is_rejected():
    r = run_tool("n8n_do_everything", {}, client=_client(MockTransport()),
                 capabilities=_caps("workflows"))
    assert not r["success"] and r["error"]["type"] == "unknown_tool"
