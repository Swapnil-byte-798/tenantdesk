import os
import unittest
from tenantdesk.postgres import PostgresStore
from tenantdesk.service import TenantService


@unittest.skipUnless(
    os.environ.get("TENANTDESK_TEST_RUNTIME_DSN"),
    "PostgreSQL RLS integration runs in its CI job",
)
class PostgresRlsTests(unittest.TestCase):
    def setUp(self):
        self.store = PostgresStore(
            os.environ["TENANTDESK_TEST_RUNTIME_DSN"],
            os.environ["TENANTDESK_TEST_ADMIN_DSN"],
        )
        self.store.initialize()
        self.service = TenantService(store=self.store)
        self.a = self.service.create_tenant("RLS A")
        self.b = self.service.create_tenant("RLS B")
        self.service.put_document(
            self.a["tenant_token"],
            "secret",
            "Policy",
            "Workspace A secret return period is fourteen days.",
        )
        self.service.put_document(
            self.b["tenant_token"],
            "secret",
            "Policy",
            "Workspace B secret return period is thirty days.",
        )

    def tearDown(self):
        with self.store.transaction(admin=True) as connection:
            connection.execute(
                "DELETE FROM tenants WHERE id IN (?,?)", (self.a["id"], self.b["id"])
            )

    def test_unscoped_runtime_connection_cannot_read_documents(self):
        with self.store.transaction() as connection:
            self.assertEqual(
                connection.execute("SELECT * FROM documents").fetchall(), []
            )

    def test_database_policy_filters_cross_tenant_select(self):
        with self.store.transaction(self.a["id"]) as connection:
            rows = connection.execute("SELECT * FROM documents").fetchall()
            self.assertEqual(len(rows), 1)
            self.assertIn("Workspace A", rows[0]["text"])
            self.assertEqual(
                connection.execute(
                    "SELECT * FROM documents WHERE tenant_id=?", (self.b["id"],)
                ).fetchall(),
                [],
            )

    def test_database_policy_rejects_cross_tenant_insert(self):
        import psycopg

        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.store.transaction(self.a["id"]) as connection:
                connection.execute(
                    "INSERT INTO documents VALUES(?,?,?,?)",
                    (self.b["id"], "forbidden", "Wrong", "Cross tenant write"),
                )

    def test_real_postgres_chat_and_quota(self):
        result = self.service.chat(
            self.a["tenant_token"], "What is the return period?", "one"
        )
        self.assertIn("fourteen", result["answer"])
        self.assertNotIn("thirty", result["answer"])
