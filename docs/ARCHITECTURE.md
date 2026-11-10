# TenantDesk: architecture

## Request and data path

Verified tenant token → scoped document retrieval → quota admission → cited answer or handoff → tenant conversation export

`api.py` validates transport input and credentials. `service.py` owns domain invariants and SQL transitions. `runtime.py` supplies small, vendored transport/configuration conventions so the repository can install independently. `cli.py` exposes setup, a labelled demo and serving commands. SQL schemas live beside the service that owns them.

## Decisions

Python and SQL keep the project aligned with the portfolio's existing skills. FastAPI supplies an inspectable contract without authored web code. SQLite provides a durable, low-cost local path; it is not a distributed database. The service owns transaction boundaries rather than spreading writes across API handlers. Domain services accept provider fixtures for tests; production commands never replace failed upstream calls with fixtures.

Provider keys come from owner-only files or the process environment. Tokens are distinct from provider keys. Never put a provider key into a public API client's configuration. Concurrent SQL writes are admitted transactionally; processes that die during external work can require operator recovery rather than unsafe automatic replay.

## Failure boundaries

1. Tenant identity is derived from a verified token, never a request body's tenant ID.
2. Documents, answer caches, leads and exports must remain tenant-scoped.
3. Concurrent admissions cannot exceed a tenant's quota.
4. PostgreSQL runtime queries without context must see no tenant rows.

Missing credentials return a configuration failure. Invalid provider structures fail validation. Network requests have timeouts and no silent retries through the common JSON client. An upstream timeout can still consume provider tokens; local rollback cannot undo external billing.

## Capacity and security limits

This version exposes a Python API rather than a JavaScript embed widget. Quotas are lifetime message allocations, not recurring subscription allowances. Leads are stored with consent; no email is sent. SQLite isolation is enforced by service queries; database-level RLS applies only to PostgreSQL. PostgreSQL initialization requires a privileged setup connection and a restricted runtime role. Do not expose the admin connection to clients.

Bind locally for development. Before external hosting, add TLS, gateway request-size limits, restricted egress, protected persistent storage, retention policies and a process-specific secret store. No internet-facing deployment or production security certification is claimed by this repository.
