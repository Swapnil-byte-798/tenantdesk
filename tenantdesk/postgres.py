"""The same service queries under a PostgreSQL runtime role and forced RLS."""

from contextlib import contextmanager
from .runtime import Fault
from .service import SCHEMA

TABLES = ("tenants", "documents", "chunks", "requests", "cache", "leads")


class Connection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, parameters=()):
        return self.connection.execute(query.replace("?", "%s"), parameters)


class PostgresStore:
    dialect = "postgresql"

    def __init__(self, runtime_dsn, admin_dsn):
        self.runtime_dsn = runtime_dsn
        self.admin_dsn = admin_dsn
        if not runtime_dsn or not admin_dsn:
            raise Fault(
                "Configure both PostgreSQL runtime and admin connection URLs.", 503
            )

    def initialize(self):
        import psycopg

        with psycopg.connect(self.admin_dsn) as connection:
            for statement in SCHEMA.split(";"):
                if statement.strip():
                    connection.execute(statement)
            for table in TABLES:
                column = "id" if table == "tenants" else "tenant_id"
                connection.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
                connection.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
                connection.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
                connection.execute(
                    f"CREATE POLICY tenant_isolation ON {table} USING ({column}=current_setting('app.tenant_id',true)) WITH CHECK ({column}=current_setting('app.tenant_id',true))"
                )
                connection.execute(
                    f"GRANT SELECT,INSERT,UPDATE,DELETE ON {table} TO tenantdesk_runtime"
                )
            connection.execute("""CREATE OR REPLACE FUNCTION resolve_tenant(hash TEXT) RETURNS TEXT
                LANGUAGE SQL SECURITY DEFINER SET search_path=public,pg_temp AS $$
                SELECT id FROM public.tenants WHERE token_hash=hash LIMIT 1 $$""")
            connection.execute(
                "REVOKE ALL ON FUNCTION resolve_tenant(TEXT) FROM PUBLIC"
            )
            connection.execute(
                "GRANT EXECUTE ON FUNCTION resolve_tenant(TEXT) TO tenantdesk_runtime"
            )

    @contextmanager
    def transaction(self, tenant_id=None, admin=False):
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(
            self.admin_dsn if admin else self.runtime_dsn, row_factory=dict_row
        ) as connection:
            if tenant_id is not None:
                connection.execute(
                    "SELECT set_config('app.tenant_id',%s,true)", (tenant_id,)
                )
            yield Connection(connection)

    def resolve(self, token_hash):
        with self.transaction() as connection:
            row = connection.execute(
                "SELECT resolve_tenant(?) AS id", (token_hash,)
            ).fetchone()
            return row["id"] if row else None
