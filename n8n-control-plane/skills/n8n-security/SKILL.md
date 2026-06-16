---
name: n8n-security
description: >
  Run security and governance workflows on an n8n instance: generate the built-in
  security audit, perform a full security review, and safely sync from source
  control. Use this skill WHENEVER the user asks about security posture, audits,
  risky permissions, secrets hygiene, or git-backed environments — "run a security
  audit", "are there exposed secrets", "review our n8n security", "pull the latest
  from git". Source-control pull is production-impact and always previews first;
  it never auto-continues through conflicts or deletions.
version: 1.0.0
risk_level: mixed
---

# n8n Security & Governance

Combines the instance's audit endpoint with cross-cutting checks (credentials,
access, secret-in-variable detection) and the source-control pull flow.

## When to use
- Security audit + prioritized findings → `n8n_audit_generate`, `security_review`.
- Instance-wide posture review → operation `security_review`.
- Git-backed environment sync → operation `source_control_sync`.

## Availability
`audit`, `source-control` may be edition-gated — confirm with **n8n-discovery**.

## Tools
Read: `n8n_audit_generate` (generates a report; no state change).
Production-impact: `n8n_source_control_pull`.
Operations: `security_review`, `source_control_sync`.

## Security review (operation)
`security_review` runs the audit, scans credentials, looks for over-broad
access/owners, finds secret-looking values stored as plain variables, lists
community packages, ranks production risks, and emits a remediation roadmap.

```bash
python3 -m n8n_cp op security_review
```

## Source-control sync (operation)
1. confirm capability  2. dry-run preview of changed resources  3. explicit
approval (token)  4. pull  5. report changed resources  6. post-pull health
check. Conflicts/deletions never auto-continue — they stop for human review.

```bash
python3 -m n8n_cp op source_control_sync                 # preview only
python3 -m n8n_cp op source_control_sync --confirm <TOKEN>
```

## Confirmation rules
Pull is production-impact: env flag + operation-bound token, after a dry-run.

## Forbidden
- Pulling in production without a preview + approval.
- Surfacing any secret discovered during the review (findings are redacted).

## Examples
- "How healthy/secure is our n8n?" → `security_review` → findings + roadmap.
- "Promote staging to prod via git" → `source_control_sync` preview → confirm.
