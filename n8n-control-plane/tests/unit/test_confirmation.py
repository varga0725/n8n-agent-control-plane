import time

from n8n_cp.core import confirmation as c


def test_token_roundtrip_ok():
    tok = c.issue_token("workflow.delete", "128")
    ok, reason = c.verify_token(tok, "workflow.delete", "128")
    assert ok and reason == ""


def test_token_bound_to_resource():
    tok = c.issue_token("workflow.delete", "128")
    ok, _ = c.verify_token(tok, "workflow.delete", "999")
    assert not ok


def test_token_bound_to_operation():
    tok = c.issue_token("workflow.delete", "128")
    ok, _ = c.verify_token(tok, "workflow.activate", "128")
    assert not ok


def test_expired_token_rejected():
    tok = c.issue_token("workflow.delete", "128", ttl_s=-1)
    ok, reason = c.verify_token(tok, "workflow.delete", "128")
    assert not ok and "expired" in reason.lower()


def test_malformed_token_rejected():
    ok, _ = c.verify_token("not-a-real-token", "workflow.delete", "128")
    assert not ok
