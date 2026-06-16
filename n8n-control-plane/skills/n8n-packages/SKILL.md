---
name: n8n-packages
description: >
  Manage n8n community packages (install/list/update/uninstall) and, when enabled,
  the beta n8n-packages export/import. Use this skill WHENEVER the user installs
  custom nodes, manages community packages, or moves workflows as packages —
  "install n8n-nodes-foo", "what packages are installed", "update this node
  package", "export these workflows as a package". Production auto-install is
  forbidden; before uninstalling, find workflows that use the package's nodes;
  the beta n8n-packages feature only activates if discovery shows it enabled.
version: 1.0.0
risk_level: mixed
---

# n8n Packages

Two related areas: community packages (custom nodes) and the beta n8n-packages
bundles for moving workflows between instances/projects.

## Availability
- Community packages may be disabled on managed instances.
- `n8n-packages` (export/import) is **beta**, off by default; it only works when
  `N8N_PUBLIC_API_PACKAGES_ENABLED=true` AND **n8n-discovery** reports it
  available. Do not attempt it otherwise.

## Tools
Read: `n8n_community_package_list`.
Production-impact: `n8n_community_package_install`, `n8n_community_package_update`,
`n8n_package_import` (beta).
Reversible: `n8n_package_export` (beta).
Destructive: `n8n_community_package_uninstall`.

## Pre-checks
- Install → validate package name + version; identify affected workflows; never
  auto-install in production.
- Update → identify workflows depending on the package first.
- Uninstall → find workflows using the package's nodes (they will break).
- Import (beta) → validate the package, detect workflow conflicts, check
  credential dependencies, validate the target project, produce an import plan.

## Confirmation rules
Install/update/import are production-impact; uninstall is destructive. All require
the env flag + an operation-bound token. Every package action is audited.

## Forbidden
- Auto-installing packages in production.
- Uninstalling without surfacing dependent workflows.
- Using beta n8n-packages without confirmed capability.

## Examples
- "Install n8n-nodes-pdf 1.2.0" → validate ref → show affected scope → confirm.
- "Export the Finance workflows as a package" (beta) → confirm capability →
  `n8n_package_export` with the workflow IDs.
