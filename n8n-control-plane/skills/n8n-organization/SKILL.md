---
name: n8n-organization
description: >
  Organize an n8n instance with tags, folders, and variables: create, list,
  rename/update, and delete them. Use this skill WHENEVER the user tidies or
  structures their instance — "tag these workflows", "make a folder for finance
  flows", "set an env variable", "rename this tag", "clean up unused tags". Tag
  names are de-duplicated on create; secret-looking variable values are flagged
  (store secrets as credentials instead); deletes are destructive.
version: 1.0.0
risk_level: mixed
---

# n8n Organization (tags, folders, variables)

Light-touch structural metadata. Mostly low risk, but deletes are destructive and
variables must never become a place to stash secrets.

## When to use
- Tags: create/list/get/rename/delete; apply to workflows/executions (tag IDs are
  set via the workflow/execution skills).
- Folders: create/list/get/update/delete within a project.
- Variables: create/list/update/delete instance variables.

## Tools
Tags: `n8n_tag_create` (dedup), `n8n_tag_list`, `n8n_tag_get`, `n8n_tag_update`,
`n8n_tag_delete`.
Folders: `n8n_folder_list`, `n8n_folder_create`, `n8n_folder_get`,
`n8n_folder_update`, `n8n_folder_delete` (contents check).
Variables: `n8n_variable_list`, `n8n_variable_create`, `n8n_variable_update`,
`n8n_variable_delete`.

## Pre-checks
- Tag create → check for an existing tag of the same name first.
- Folder delete → check the folder's contents; move/delete children first.
- Variable create/update → if the value looks secret-like, warn and recommend a
  credential or secret manager instead.
- Variable delete → search for where it may be used first.

## Confirmation rules
All deletes are destructive (env flag + token). Creates/updates are reversible.

## Forbidden
- Storing real secrets as plain variables.
- Deleting a non-empty folder without addressing its contents.

## Examples
- "Create a 'finance' tag" → `n8n_tag_create` (warns if it already exists).
- "Set variable REGION=eu-central" → `n8n_variable_create`.
- "Delete the 'temp' folder in project p_3" → `n8n_folder_delete` (contents
  check) → confirm.
