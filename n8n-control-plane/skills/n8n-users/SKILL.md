---
name: n8n-users
description: >
  Manage n8n users and global roles: list, look up by id/email, create (incl.
  bulk), change global role, and delete. Use this skill WHENEVER the user manages
  people/accounts/roles on the instance — "add these teammates", "make X an
  admin", "who are the owners", "remove this user". Creating users and changing
  roles are access changes (production-impact); deleting a user is destructive.
  Owner role changes and owner deletion are especially high risk.
version: 1.0.0
risk_level: mixed
---

# n8n Users

User and role management changes who can do what. Treat every change as an
access-control decision.

## When to use
- Listing users; finding a user by id or email.
- Creating one or many users; changing a user's global role; deleting a user.

## When NOT to use
- Project membership/roles → **n8n-projects** (project-scoped users).

## Tools
Read: `n8n_user_list`, `n8n_user_get`.
Production-impact: `n8n_user_create` (dedups emails), `n8n_user_update_role`
(owner guard).
Destructive: `n8n_user_delete` (owner-delete guard).

## Pre-checks
- Role change → fetch the user's current role first; flag owner changes.
- Bulk create → check for email duplicates before creating.
- Delete → guard against deleting an owner (can orphan resources).

## Confirmation rules
Create, role change, delete all require the relevant env flag + an
operation-bound confirmation token. Owner-affecting changes get an extra warning
in the impact summary.

## Forbidden
- Silently elevating privileges.
- Deleting an owner without explicit, informed confirmation.

## Examples
- "Add alice@co.com and bob@co.com as members" → `n8n_user_create` (emails
  deduped) → confirm.
- "Make user 7 an admin" → `n8n_user_get` (current role) → `n8n_user_update_role`
  → confirm.
