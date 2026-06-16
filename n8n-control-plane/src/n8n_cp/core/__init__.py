"""Core infrastructure for the n8n control plane.

These modules are transport- and domain-agnostic. They implement the
cross-cutting concerns every API call must respect: configuration, auth,
secret redaction, error normalization, risk classification, retry, audit
logging, confirmation, pagination, capability discovery, diffing and backup.
"""
