# PostgreSQL deployment and row security

Install with `python -m pip install -e ".[postgres,dev]"`. Use a dedicated empty PostgreSQL database and a separate `tenantdesk_runtime` login with NOSUPERUSER, NOBYPASSRLS and no table ownership. The administration connection must be a trusted database administrator able to perform setup and tenant provisioning; never distribute it with tenant tokens.

Set TENANTDESK_DATABASE_URL to the restricted runtime connection and TENANTDESK_ADMIN_DATABASE_URL to the administrator connection through your local secret environment. Both setting names can also appear in the ignored `.env`. Run:

```bash
python -m tenantdesk init-postgres
python -m tenantdesk serve
```

Initialization creates the schema, enables and forces row security, grants runtime DML privileges, and installs a narrowly scoped SECURITY DEFINER token-resolution function. In this version its owner must be able to bypass RLS to resolve a hashed token before tenant context is known; CI uses the postgres administrator. Tenant creation also uses the privileged connection. All knowledge, quota and conversation operations use the restricted connection.

The server verifies a tenant token, resolves its tenant ID, then sets transaction-local `app.tenant_id`. RLS policies check that context for reads and writes. Application queries also include the tenant ID. An unscoped runtime transaction sees no tenant rows. Transaction-local settings avoid leaking one request's tenant to another connection.

CI provisions PostgreSQL 16, creates the restricted runtime role, and runs real isolation tests. To repeat them locally, set TENANTDESK_TEST_ADMIN_DSN and TENANTDESK_TEST_RUNTIME_DSN against a disposable test database and run `python -m pytest tests/test_postgres_rls.py -q`. These tests create and remove their own tenants. SQLite tests cannot establish PostgreSQL RLS correctness.

The runtime role must not accept arbitrary SQL from users. RLS does not protect data from administrators, database owners with bypass privileges, or an attacker controlling server code and its privileged configuration.
