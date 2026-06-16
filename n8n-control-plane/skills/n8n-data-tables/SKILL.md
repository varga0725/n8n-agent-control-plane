---
name: n8n-data-tables
description: >
  Manage n8n Data Tables and their rows/columns: create/list/update/delete tables,
  list rows, batch insert, update, upsert, delete rows by filter, and manage
  columns. Use this skill WHENEVER the user works with n8n Data Tables —
  "add rows to the table", "update records where status=pending", "delete old
  rows", "add a column". Bulk row deletes with an empty/too-broad filter are
  refused outright; column deletion warns about permanent data loss; large reads
  are paginated and bounded.
version: 1.0.0
risk_level: mixed
---

# n8n Data Tables

Data Tables hold real data, so the dangerous operations here are bulk mutations.
The hard rules exist to prevent accidental mass data loss.

## When to use
- Managing tables; reading/inserting/updating/upserting/deleting rows; managing
  columns.

## Availability
Data Tables are an optional feature — confirm with **n8n-discovery** first
(`capability_unavailable` means it's off on this instance).

## Tools
Read: `n8n_data_table_list`, `n8n_data_table_get`, `n8n_data_table_row_list`,
`n8n_data_table_column_list`.
Reversible: `n8n_data_table_create`, `n8n_data_table_update`,
`n8n_data_table_row_insert`, `n8n_data_table_row_update` (filter required),
`n8n_data_table_row_upsert`, `n8n_data_table_column_create`,
`n8n_data_table_column_update`.
Destructive: `n8n_data_table_delete`, `n8n_data_table_row_delete` (filter
required + count preview), `n8n_data_table_column_delete` (data-loss warning).

## Hard rules (refused outright)
- Row **delete** with an empty/absent filter → rejected (would wipe the table).
- Row **update** without a filter → rejected (would touch every row).
- Large `row_list` → paginated with the global ceiling; never unbounded.

## Pre-checks
- Row delete → preview the count of matching rows before deleting.
- Column delete → warn that the column's data is permanently lost from every row.
- Bulk update → validate the filter.

## Confirmation rules
Table/row/column deletes are destructive (env flag + token). Inserts/upserts in a
narrow scope are reversible writes.

## Examples
- "Delete rows where status = 'archived'" → `n8n_data_table_row_delete` with an
  explicit filter → it previews the count and issues a token → confirm.
- "Wipe the table" with no filter → refused; ask for a specific filter or an
  explicit table delete.
