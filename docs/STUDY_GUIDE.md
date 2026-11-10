# TenantDesk: study guide

## Explain the problem

Knowledge assistants with a tenant boundary at every storage operation. Explain who uses the workflow and why each confirmation, isolation or validation boundary exists before describing libraries.

## Read the implementation

1. Read `service.py` and its SQL schema. Name the durable entities and draw their valid state transitions.
2. Trace one successful API request from its Pydantic input to its committed writes.
3. Trace a provider failure and identify what can and cannot be rolled back.
4. Read the tests that enforce the acceptance conditions below. Explain why each failure would matter to a user.

1. Tenant identity is derived from a verified token, never a request body's tenant ID.
2. Documents, answer caches, leads and exports must remain tenant-scoped.
3. Concurrent admissions cannot exceed a tenant's quota.
4. PostgreSQL runtime queries without context must see no tenant rows.

## Interview discussion

- Where is the transaction boundary, and what happens if the process dies immediately after it?
- How are retries bound to the original request? Which operation can safely repeat?
- Which inputs are untrusted, and how are externally generated fields validated?
- What is tested with fixtures, what was measured on public data, and what remains unmeasured?
- What would change with ten times the data, multiple workers, or another tenant?

## Honest project explanation

Describe the implemented behavior, then demonstrate a representative test and explain its failure condition. Do not present mock latency, authored examples, uncalibrated scores or optional integrations as measured production results.

Known boundaries: This version exposes a Python API rather than a JavaScript embed widget. Quotas are lifetime message allocations, not recurring subscription allowances. Leads are stored with consent; no email is sent. SQLite isolation is enforced by service queries; database-level RLS applies only to PostgreSQL. PostgreSQL initialization requires a privileged setup connection and a restricted runtime role. Do not expose the admin connection to clients.

## Practical extension

Add token rotation, data retention controls and an isolated ingestion worker before a multi-customer deployment. Define a measurable acceptance criterion before extending the implementation.
