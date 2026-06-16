---
name: n8n-projects
description: >
  Manage n8n projects and their membership: create, list, update, delete
  projects, and add/remove/role-change project members. Use this skill WHENEVER
  the user organizes work into projects or manages who belongs to a project —
  "create a Finance project", "add the team to this project", "what's in project
  X", "delete the old project". Deleting a project is destructive and refused
  while it still contains resources; member additions/role changes are
  production-impact. For end-to-end setup use the project_bootstrap operation.
version: 1.0.0
risk_level: mixed
---

# n8n Projects

Projects are the unit of isolation for workflows, credentials, folders and data
tables. Deleting one can remove a lot at once, so deletion is heavily guarded.

## When to use
- Creating/listing/updating projects; managing project members and their roles.
- Standing up a new project with members, folders, tags, variables →
  operation `project_bootstrap`.

## Tools
Read: `n8n_project_list`, `n8n_project_user_list`.
Reversible: `n8n_project_create`, `n8n_project_update`.
Production-impact: `n8n_project_user_add`, `n8n_project_user_update_role`.
Destructive: `n8n_project_delete`, `n8n_project_user_remove`.
Operation: `project_bootstrap`.

## Pre-checks
- Project delete → take a full inventory first (workflows, credentials, folders,
  users, data tables). A non-empty project is **not** auto-deleted.
- Member add / role change → these are access changes; confirm.

## Confirmation rules
Delete (destructive) and member/role changes (production-impact) require the env
flag + an operation-bound token. The delete impact summary lists the inventory.

## Forbidden
- Auto-deleting a non-empty project.
- Silent membership/role changes.

## Examples
- "Spin up a Finance project with Alice as admin and a Reports folder" →
  `project_bootstrap --json '{"name":"Finance","users":[{"email":"alice@co.com","role":"admin"}],"folders":["Reports"]}'`.
- "Delete project p_42" → `n8n_project_delete --param projectId=p_42 --dry-run`
  (shows inventory + token) → confirm only if truly intended.
