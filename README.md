# TenantDesk

Knowledge assistants with a tenant boundary at every storage operation.

[![Python verification](https://github.com/Swapnil-byte-798/tenantdesk/actions/workflows/ci.yml/badge.svg)](https://github.com/Swapnil-byte-798/tenantdesk/actions/workflows/ci.yml)

Project 10 in a Python and SQL AI engineering portfolio. The interface is a Python CLI and FastAPI's generated API documentation.

## What works

- Tenant-scoped knowledge, caches, conversations, quotas and consented leads
- Keyless extractive answers and optional verified LLM source quotations
- SQLite for local use and a wired PostgreSQL adapter with forced row security
- Server-derived tenant context, hashed tokens and isolated data export

## Run it

Python 3.11 or 3.12. PostgreSQL is optional: install .[postgres,dev] and follow docs/POSTGRES.md.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q
python -m tenantdesk demo
python -m tenantdesk setup
python -m tenantdesk serve --port 8020
```

Open http://127.0.0.1:8020/docs. `setup` prompts for credentials without displaying them, generates independent operator/reviewer tokens, and stores them in an ignored file with owner-only permissions. Use the operator token as `Authorization: Bearer ...`; account, client and tenant endpoints issue their own scoped tokens. Do not commit any of these values.

The demo is explicitly labelled: authored fixtures exercise the workflow, not a live provider. `check-keys` reports configuration only and never claims a provider has been validated.

## Credentials

No key for extractive answers. GROQ_API_KEY is optional for live quote selection. PostgreSQL deployment also needs runtime and admin DSNs.

To reuse a provider key across these repositories, run `python -m tenantdesk setup --shared` before the local `setup` command. The shared prompt adds missing keys and preserves existing nonempty keys. Local environment variables take precedence. See [.env.example](.env.example) for names only; real keys are never shipped.

## Design and boundaries

Verified tenant token → scoped document retrieval → quota admission → cited answer or handoff → tenant conversation export

This version exposes a Python API rather than a JavaScript embed widget. Quotas are lifetime message allocations, not recurring subscription allowances. Leads are stored with consent; no email is sent. SQLite isolation is enforced by service queries; database-level RLS applies only to PostgreSQL. PostgreSQL initialization requires a privileged setup connection and a restricted runtime role. Do not expose the admin connection to clients.

## Verification

Cross-tenant retrieval and export, prompt injection boundaries, quota contention, cache invalidation, consent checks and a separate real PostgreSQL RLS integration job. Common tests also cover hidden setup, configuration precedence, provider response validation, API authentication and transactional rollback.

[Verification record](evidence/verification.json) separates automated checks from provider-dependent acceptance. No result represents all possible inputs, production load, or a calibrated model-quality benchmark.

## Read further

- [Requirements and acceptance](docs/REQUIREMENTS.md)
- [Architecture and decisions](docs/ARCHITECTURE.md)
- [Runbook and key setup](docs/RUNBOOK.md)
- [Study guide](docs/STUDY_GUIDE.md)

## Next engineering milestone

Add token rotation, data retention controls and an isolated ingestion worker before a multi-customer deployment.
