from n8n_cp.core import retry, pagination
from n8n_cp.core.diff import workflow_diff


def test_retry_status_classification():
    assert retry.is_retryable_status(429)
    assert retry.is_retryable_status(503)
    assert not retry.is_retryable_status(400)
    assert not retry.is_retryable_status(404)


def test_backoff_schedule_increases_and_honors_retry_after():
    d1 = retry.backoff_delay_ms(1)
    d2 = retry.backoff_delay_ms(2)
    assert 500 <= d1 < 1500
    assert d2 >= 1500
    assert retry.backoff_delay_ms(1, retry_after_s=10) == 10000


def test_clamp_limit_bounds():
    assert pagination.clamp_limit(None) == pagination.DEFAULT_LIMIT
    assert pagination.clamp_limit(0) == pagination.DEFAULT_LIMIT
    assert pagination.clamp_limit(99999) == 250


def test_collect_respects_max_items():
    pages = [{"data": list(range(100)), "nextCursor": "c1"},
             {"data": list(range(100)), "nextCursor": "c2"},
             {"data": list(range(100)), "nextCursor": None}]
    state = {"i": 0}

    def fetch(cursor):
        p = pages[state["i"]]
        state["i"] += 1
        return p

    items, nxt, truncated = pagination.collect(fetch, max_items=150)
    assert len(items) == 150 and truncated


def test_workflow_diff_detects_changes():
    old = {"nodes": [{"name": "A", "type": "n8n-nodes-base.set", "parameters": {}}],
           "connections": {}, "active": True}
    new = {"nodes": [{"name": "A", "type": "n8n-nodes-base.set", "parameters": {"x": 1}},
                     {"name": "Hook", "type": "n8n-nodes-base.webhook", "parameters": {}}],
           "connections": {"A": {"main": [[]]}}, "active": True}
    d = workflow_diff(old, new)
    assert "Hook" in d["nodesAdded"]
    assert "A" in d["nodesModified"]
    assert d["connectionsChanged"] is True
    assert "Hook" in d["triggerOrWebhookOrScheduleChanges"]
