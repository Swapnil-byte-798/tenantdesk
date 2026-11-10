# TenantDesk: requirements and acceptance

## Product goal

Knowledge assistants with a tenant boundary at every storage operation. A reviewer should be able to install the package, run its tests, inspect its SQL boundaries and exercise the core workflow without a custom frontend.

## Functional requirements

- Tenant-scoped knowledge, caches, conversations, quotas and consented leads
- Keyless extractive answers and optional verified LLM source quotations
- SQLite for local use and a wired PostgreSQL adapter with forced row security
- Server-derived tenant context, hashed tokens and isolated data export

## Acceptance conditions

1. Tenant identity is derived from a verified token, never a request body's tenant ID.
2. Documents, answer caches, leads and exports must remain tenant-scoped.
3. Concurrent admissions cannot exceed a tenant's quota.
4. PostgreSQL runtime queries without context must see no tenant rows.

## Quality requirements

Persist domain state transactionally; validate untrusted inputs; keep provider failures visible; avoid credential and prompt disclosure in diagnostic errors; provide an installable Python package, authenticated API, container and repeatable automated checks. Keep fixture evidence distinct from public-data and live-provider evidence.

## Scope boundary

This version exposes a Python API rather than a JavaScript embed widget. Quotas are lifetime message allocations, not recurring subscription allowances. Leads are stored with consent; no email is sent. SQLite isolation is enforced by service queries; database-level RLS applies only to PostgreSQL. PostgreSQL initialization requires a privileged setup connection and a restricted runtime role. Do not expose the admin connection to clients.

## Evaluation plan

Cross-tenant retrieval and export, prompt injection boundaries, quota contention, cache invalidation, consent checks and a separate real PostgreSQL RLS integration job. External checks need the credentials, model files or network access described in the runbook. Before publishing quality claims, create a labelled evaluation set and report sample size, metric definition, model version and measured failures. Add token rotation, data retention controls and an isolated ingestion worker before a multi-customer deployment.
