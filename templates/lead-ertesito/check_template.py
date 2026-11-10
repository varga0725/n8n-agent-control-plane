#!/usr/bin/env python3
"""Offline checks for the Lead-értesítő template.

Structural validation uses n8n-workflow-builder/scripts/validate_workflow.py.
Mapping expressions are executed with Node against form and webhook payloads.
No network call to an n8n instance.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCRIPTS = ROOT / "n8n-workflow-builder" / "scripts"
MAIN = HERE / "lead-ertesito.json"
ERROR = HERE / "lead-ertesito-hibakezelo.json"

FORBIDDEN = (
    "tail1d007c",
    "ts.net",
    "tailscale",
    "sk-",
    "xoxb-",
    "AIza",
    "BEGIN PRIVATE",
    "ya29.",
    "ghp_",
    "xoxp-",
)

PLACEHOLDERS = (
    "COMPANY_NAME",
    "FROM_NAME",
    "OWNER_EMAIL",
    "REPLY_SUBJECT",
    "REPLY_BODY_TEMPLATE",
    "YOUR_SHEET_ID",
    "YOUR_CHAT_ID",
    "FORM_TITLE",
    "FORM_DESCRIPTION",
    "FORM_THANK_YOU",
    "FIELD_NAME",
    "FIELD_EMAIL",
    "FIELD_PHONE",
    "FIELD_MESSAGE",
    "FIELD_SOURCE",
    "GMAIL_OAUTH2",
    "GOOGLE_SHEETS_OAUTH2",
    "TELEGRAM_BOT_TOKEN",
    "ERROR_WORKFLOW_ID",
)

SHEET_HEADERS = ["Időpont", "Név", "Email", "Telefon", "Üzenet", "Forrás"]


def load_validator():
    sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / "validate_workflow.py"
    spec = importlib.util.spec_from_file_location("validate_workflow", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fail(msg: str) -> None:
    print(f"ERROR {msg}")
    sys.exit(1)


def assignment(wf: dict, node_name: str, field: str) -> str:
    node = next(n for n in wf["nodes"] if n["name"] == node_name)
    for item in node["parameters"]["assignments"]["assignments"]:
        if item["name"] == field:
            return item["value"]
    fail(f"{node_name} has no assignment {field}")


def run_mapping(expr: str, payload: dict):
    body = expr.strip()
    if body.startswith("={{") and body.endswith("}}"):
        body = body[3:-2].strip()
    else:
        fail(f"expression is not an n8n expression: {expr[:40]}")
    script = (
        "const $json = JSON.parse(process.argv[2]);\n"
        "const value = eval(process.argv[3]);\n"
        "process.stdout.write(JSON.stringify(value));\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(script)
        path = handle.name
    result = subprocess.run(
        ["node", path, json.dumps(payload), body],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail(f"mapping expression failed: {result.stderr}")
    return json.loads(result.stdout)


def main() -> None:
    validator = load_validator()
    blobs = []
    for path in (MAIN, ERROR, HERE / "README.md"):
        text = path.read_text(encoding="utf-8")
        blobs.append(text)
        lowered = text.lower()
        for token in FORBIDDEN:
            if token.lower() in lowered:
                fail(f"{path.name} contains forbidden token {token}")

    main_wf = json.loads(MAIN.read_text(encoding="utf-8"))
    error_wf = json.loads(ERROR.read_text(encoding="utf-8"))
    joined = "\n".join(blobs)
    for token in PLACEHOLDERS:
        if token not in joined:
            fail(f"missing placeholder {token}")

    for wf in (main_wf, error_wf):
        errors, warnings = validator.validate(wf)
        unexpected = [
            w
            for w in warnings
            if "Megjegyzés" not in w and "no connections" not in w
        ]
        if errors or unexpected:
            fail(f"structural validation failed: {errors} {unexpected}")
        if wf["settings"].get("timezone") != "Europe/Budapest":
            fail("timezone must be Europe/Budapest")
        if wf["settings"].get("executionOrder") != "v1":
            fail("executionOrder must be v1")

    by_name = {n["name"]: n for n in main_wf["nodes"]}
    expect_versions = {
        "Új lead (űrlap)": ("n8n-nodes-base.formTrigger", 2.2),
        "Webhook (POST)": ("n8n-nodes-base.webhook", 2),
        "Adatok normalizálása": ("n8n-nodes-base.set", 3.4),
        "Van érvényes e-mail?": ("n8n-nodes-base.if", 2.2),
        "Automatikus válasz a leadnek": ("n8n-nodes-base.gmail", 2.1),
        "Lead mentése (Google Sheets)": ("n8n-nodes-base.googleSheets", 4.5),
        "Értesítés a tulajdonosnak": ("n8n-nodes-base.telegram", 1.2),
        "Válasz 200 OK": ("n8n-nodes-base.respondToWebhook", 1.4),
    }
    for name, (ntype, version) in expect_versions.items():
        node = by_name[name]
        if node["type"] != ntype or node["typeVersion"] != version:
            fail(f"{name} is {node['type']}@{node['typeVersion']}")

    form = by_name["Új lead (űrlap)"]["parameters"]
    labels = [f["fieldLabel"] for f in form["formFields"]["values"]]
    if labels != ["Név", "Email", "Telefon", "Üzenet"]:
        fail(f"unexpected form fields {labels}")
    if form["responseMode"] != "onReceived":
        fail("form must answer on submit")
    if form["options"]["respondWithOptions"]["values"]["formSubmittedText"] != "FORM_THANK_YOU":
        fail("form thank-you placeholder missing")

    webhook = by_name["Webhook (POST)"]["parameters"]
    if webhook["httpMethod"] != "POST" or webhook["responseMode"] != "responseNode":
        fail("webhook must be POST with responseNode")
    respond = by_name["Válasz 200 OK"]["parameters"]
    if respond["options"].get("responseCode") != 200:
        fail("webhook response must be 200")

    fanout = [
        t["node"]
        for t in main_wf["connections"]["Adatok normalizálása"]["main"][0]
    ]
    if fanout != [
        "Van érvényes e-mail?",
        "Lead mentése (Google Sheets)",
        "Értesítés a tulajdonosnak",
        "Értesítés a tulajdonosnak (e-mail)",
    ]:
        fail(f"normalize fan-out is {fanout}")
    if main_wf["connections"]["Van érvényes e-mail?"]["main"][1] != []:
        fail("invalid email branch must not send a reply")

    for name in (
        "Automatikus válasz a leadnek",
        "Lead mentése (Google Sheets)",
        "Értesítés a tulajdonosnak",
        "Értesítés a tulajdonosnak (e-mail)",
    ):
        if by_name[name].get("onError") != "continueErrorOutput":
            fail(f"{name} must keep sibling branches alive")
        if main_wf["connections"][name]["main"][1][0]["node"] != "Ághiba adatok":
            fail(f"{name} error output is not wired")

    owner = by_name["Értesítés a tulajdonosnak (e-mail)"]
    if owner.get("disabled") is not True:
        fail("owner email must ship disabled")

    if main_wf["settings"].get("errorWorkflow") != "ERROR_WORKFLOW_ID":
        fail("error workflow placeholder missing")
    if by_name["Ághiba jelzése"]["parameters"]["workflowId"]["value"] != "ERROR_WORKFLOW_ID":
        fail("branch errors must call ERROR_WORKFLOW_ID")

    creds = []
    for node in main_wf["nodes"] + error_wf["nodes"]:
        for cred_type, cred in (node.get("credentials") or {}).items():
            creds.append((cred_type, cred["id"], cred["name"]))
    allowed_creds = {
        ("gmailOAuth2", "GMAIL_OAUTH2", "GMAIL_OAUTH2"),
        ("googleSheetsOAuth2Api", "GOOGLE_SHEETS_OAUTH2", "GOOGLE_SHEETS_OAUTH2"),
        ("telegramApi", "TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN"),
    }
    if set(creds) != allowed_creds:
        fail(f"unexpected credentials {creds}")

    columns = by_name["Lead mentése (Google Sheets)"]["parameters"]["columns"]
    if list(columns["value"]) != SHEET_HEADERS:
        fail(f"sheet columns {list(columns['value'])}")
    if columns["schema"] and [c["id"] for c in columns["schema"]] != SHEET_HEADERS:
        fail("sheet schema headers drifted")
    if by_name["Lead mentése (Google Sheets)"]["parameters"]["sheetName"]["value"] != "Leadek":
        fail("default tab must be Leadek")

    types = " ".join(n["type"] for n in main_wf["nodes"])
    for banned in ("gmailTrigger", "twilio", "messageBird", "sms"):
        if banned.lower() in types.lower():
            fail(f"v1 must not include {banned}")

    err_names = {n["name"] for n in error_wf["nodes"]}
    for required in ("Error Trigger", "Ághiba hívás", "Tulajdonos Telegram", "Tulajdonos e-mail"):
        if required not in err_names:
            fail(f"error workflow missing {required}")
    trigger = next(n for n in error_wf["nodes"] if n["name"] == "Ághiba hívás")
    if trigger["parameters"].get("inputSource") != "passthrough":
        fail("error sub-workflow must accept all input data")

    form_payload = {
        "Név": " Anna ",
        "Email": " Anna@Example.COM ",
        "Telefon": " +36 1 ",
        "Üzenet": " Szia ",
        "submittedAt": "2026-11-10T09:00:00.000Z",
    }
    webhook_payload = {
        "headers": {},
        "body": {
            "name": " Béla ",
            "email": "BELA@ceg.hu",
            "phone": " 1 ",
            "message": " ajánlat ",
            "source": " elementor ",
        },
    }
    nested_payload = {"body": {"form_fields": {"FIELD_NAME": "Cecil", "FIELD_EMAIL": "C@D.HU"}}}
    cases = {
        "name": (form_payload, "Anna", webhook_payload, "Béla", nested_payload, "Cecil"),
        "email": (
            form_payload,
            "anna@example.com",
            webhook_payload,
            "bela@ceg.hu",
            nested_payload,
            "c@d.hu",
        ),
        "phone": (form_payload, "+36 1", webhook_payload, "1"),
        "message": (form_payload, "Szia", webhook_payload, "ajánlat"),
        "source": (form_payload, "form", webhook_payload, "elementor", nested_payload, "webhook"),
    }
    for field, values in cases.items():
        expr = assignment(main_wf, "Adatok normalizálása", field)
        it = iter(values)
        for payload, expected in zip(it, it):
            got = run_mapping(expr, payload)
            if got != expected:
                fail(f"{field} for {payload} returned {got!r}, expected {expected!r}")

    missing_email = run_mapping(
        assignment(main_wf, "Adatok normalizálása", "email"),
        {"Név": "Névtelen", "Üzenet": "nincs cím"},
    )
    if missing_email != "":
        fail("missing email must normalize to empty string")

    import re

    pattern = by_name["Van érvényes e-mail?"]["parameters"]["conditions"]["conditions"][0]["rightValue"]
    if re.search(pattern, "anna@example.com") is None:
        fail("valid email rejected")
    if re.search(pattern, "") is not None or re.search(pattern, "nem-email") is not None:
        fail("invalid email accepted")

    deep_errors, deep_warnings, checked = validator.deep_check(main_wf)
    err_errors, err_warnings, err_checked = validator.deep_check(error_wf)
    deep_errors += err_errors
    deep_warnings += err_warnings
    checked += err_checked
    gmail_nodes = {
        "Automatikus válasz a leadnek",
        "Értesítés a tulajdonosnak (e-mail)",
        "Tulajdonos e-mail",
    }
    for warn in list(deep_warnings):
        # Gmail v2.1 fields (sendTo, emailType) are absent from the community
        # schema, which still describes Gmail v1 only.
        if "unknown top-level parameter" in warn and any(name in warn for name in gmail_nodes):
            deep_warnings.remove(warn)
    for err in deep_errors:
        if "typeVersion 2.1 not in available" in err and any(name in err for name in gmail_nodes):
            continue
        fail(f"unexpected deep error: {err}")
    for warn in deep_warnings:
        if "unknown top-level parameter" in warn:
            fail(f"unexpected deep warning: {warn}")

    print(
        f"OK lead-ertesito ({len(main_wf['nodes'])} nodes) + "
        f"hibakezelo ({len(error_wf['nodes'])} nodes), deep-checked {checked}"
    )


if __name__ == "__main__":
    main()
