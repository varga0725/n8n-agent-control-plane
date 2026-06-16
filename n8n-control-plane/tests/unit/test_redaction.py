from n8n_cp.core.redaction import redact, REDACTED


def test_redacts_common_secret_keys():
    out = redact({"apiKey": "x", "password": "y", "token": "z", "name": "ok"})
    assert out["apiKey"] == REDACTED
    assert out["password"] == REDACTED
    assert out["token"] == REDACTED
    assert out["name"] == "ok"


def test_redaction_is_recursive_over_lists_and_dicts():
    data = {"nodes": [{"credentials": {"slackApi": {"token": "secret"}}}]}
    out = redact(data)
    assert out["nodes"][0]["credentials"] == REDACTED  # 'credentials' key masked


def test_confirmation_token_is_allowlisted():
    out = redact({"confirmationToken": "abc123"})
    assert out["confirmationToken"] == "abc123"


def test_case_and_separator_insensitive():
    out = redact({"X-Api-Key": "v", "Access_Token": "v", "clientSecret": "v"})
    assert all(v == REDACTED for v in out.values())
