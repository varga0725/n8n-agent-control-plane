#!/usr/bin/env python3
"""Shared loader for machine-readable n8n node schemas.

Source: the community project `yigitkonur/n8n-schema-generator`, which auto-extracts
a JSON schema for every n8n-nodes-base node + credential and commits it to GitHub
(hourly updates as new n8n versions ship). MIT licensed. These schemas give the
exact `properties`, `availableVersions`, defaults and validation rules per node —
the thing the OpenAPI spec does NOT contain.

This module is dependency-free (urllib only). It loads a node schema from a local
directory first (offline cache) and falls back to GitHub raw. Used by
`fetch_node_schema.py` and the `--deep` mode of `validate_workflow.py`.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional

RAW_BASE = ("https://raw.githubusercontent.com/yigitkonur/"
            "n8n-schema-generator/main/schemas")


def short_name(node_type: str) -> str:
    """Map a full node type to the schema file's short name.

    n8n-nodes-base.httpRequest -> httpRequest
    @n8n/n8n-nodes-langchain.agent -> agent  (note: langchain nodes are a
    separate package and are NOT in this base-node schema set).
    """
    return node_type.rsplit(".", 1)[-1]


def is_base_node(node_type: str) -> bool:
    return node_type.startswith("n8n-nodes-base.")


def _fetch(url: str, timeout: float = 15.0) -> Optional[dict]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def load_index(schema_dir: Optional[str] = None) -> Optional[dict]:
    if schema_dir:
        p = os.path.join(schema_dir, "nodes", "_index.json")
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return _fetch(f"{RAW_BASE}/nodes/_index.json")


def load_node_schema(node_type: str, schema_dir: Optional[str] = None) -> Optional[dict]:
    """Return the schema dict for a node, or None if unavailable (e.g. langchain
    nodes, community nodes, or no network)."""
    short = short_name(node_type)
    if schema_dir:
        p = os.path.join(schema_dir, "nodes", f"{short}.json")
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return _fetch(f"{RAW_BASE}/nodes/{short}.json")


def load_credential_schema(cred_type: str, schema_dir: Optional[str] = None) -> Optional[dict]:
    if schema_dir:
        p = os.path.join(schema_dir, "credentials", f"{cred_type}.json")
        if os.path.exists(p):
            with open(p) as f:
                return json.load(f)
    return _fetch(f"{RAW_BASE}/credentials/{cred_type}.json")


def top_level_param_names(schema: dict) -> set[str]:
    return {p.get("name") for p in schema.get("properties", []) if p.get("name")}


def required_param_names(schema: dict) -> set[str]:
    return {p.get("name") for p in schema.get("properties", [])
            if p.get("required") and p.get("name")}


def available_versions(schema: dict) -> list:
    return schema.get("availableVersions") or schema.get("version") or []


def check_node(node: dict, schema: dict) -> list[tuple[str, str]]:
    """Validate one node against its schema. Returns (level, message) tuples,
    level in {"error","warn"}. Conservative: only top-level params are checked
    (nested collections vary), and unknown params are warnings, not errors."""
    out: list[tuple[str, str]] = []
    name = node.get("name", "?")

    tv = node.get("typeVersion")
    versions = available_versions(schema)
    if versions and tv is not None and tv not in versions:
        out.append(("error", f"'{name}': typeVersion {tv} not in available "
                    f"versions {versions} (default {schema.get('defaultVersion')})."))

    known = top_level_param_names(schema)
    if known:
        for pname in (node.get("parameters") or {}):
            if pname not in known:
                out.append(("warn", f"'{name}': unknown top-level parameter "
                            f"'{pname}' for node type {node.get('type')}."))
        for req in required_param_names(schema):
            if req not in (node.get("parameters") or {}):
                out.append(("warn", f"'{name}': missing required parameter '{req}'."))
    return out
