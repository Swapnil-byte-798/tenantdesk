from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from tenantdesk.runtime import Fault
from tenantdesk.service import TenantService


class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.service = TenantService(Path(self.directory.name) / "test.db")
        self.a = self.service.create_tenant("Books", quota=10)
        self.b = self.service.create_tenant("Tools", quota=10)
        self.ta, self.tb = self.a["tenant_token"], self.b["tenant_token"]
        self.service.put_document(
            self.ta, "policy", "Returns", "Books may be returned within fourteen days."
        )
        self.service.put_document(
            self.tb, "policy", "Returns", "Tools may be returned within thirty days."
        )

    def tearDown(self):
        self.directory.cleanup()

    def test_tenant_retrieval_never_returns_other_policy(self):
        first = self.service.chat(self.ta, "When may books be returned?", "one")
        second = self.service.chat(self.tb, "When may tools be returned?", "one")
        self.assertIn("fourteen", first["answer"])
        self.assertNotIn("thirty", first["answer"])
        self.assertIn("thirty", second["answer"])

    def test_same_document_id_is_independent_per_tenant(self):
        self.assertEqual(len(self.service.export(self.ta)["documents"]), 1)
        self.assertEqual(len(self.service.export(self.tb)["documents"]), 1)

    def test_cache_is_tenant_isolated(self):
        first = self.service.chat(self.ta, "When may items be returned?", "a1")
        second = self.service.chat(self.tb, "When may items be returned?", "b1")
        self.assertNotEqual(first["answer"], second["answer"])
        self.assertFalse(second["cache_hit"])

    def test_document_update_invalidates_own_cache(self):
        self.service.chat(self.ta, "When may books be returned?", "one")
        self.service.put_document(
            self.ta, "policy", "Returns", "Books may be returned within seven days."
        )
        result = self.service.chat(self.ta, "When may books be returned?", "two")
        self.assertIn("seven", result["answer"])
        self.assertFalse(result["cache_hit"])

    def test_delete_is_scoped_to_token(self):
        self.service.delete_document(self.ta, "policy")
        self.assertEqual(len(self.service.export(self.tb)["documents"]), 1)
        self.assertTrue(self.service.chat(self.ta, "Returns policy?", "one")["handoff"])

    def test_quota_does_not_affect_another_tenant(self):
        tiny = self.service.create_tenant("Small", quota=1)
        self.service.chat(tiny["tenant_token"], "Question", "one")
        with self.assertRaises(Fault):
            self.service.chat(tiny["tenant_token"], "Another question", "two")
        self.assertFalse(self.service.chat(self.ta, "books returned", "one")["handoff"])

    def test_idempotent_retry_does_not_consume_quota(self):
        self.service.chat(self.ta, "books returned", "one")
        self.service.chat(self.ta, "books returned", "one")
        self.assertEqual(self.service.tenant(self.ta)["used"], 1)

    def test_payload_bound_request_key(self):
        self.service.chat(self.ta, "books returned", "one")
        with self.assertRaises(Fault):
            self.service.chat(self.ta, "Different question", "one")

    def test_invalid_token(self):
        with self.assertRaises(Fault) as error:
            self.service.export("wrong")
        self.assertEqual(error.exception.status, 401)

    def test_lead_requires_explicit_consent(self):
        with self.assertRaises(Fault):
            self.service.capture_lead(self.ta, "Person", "person@example.test", False)

    def test_leads_are_scoped(self):
        self.service.capture_lead(self.ta, "Person", "person@example.test", True)
        self.assertEqual(len(self.service.export(self.tb)["leads"]), 0)

    def test_unsupported_question_creates_handoff(self):
        result = self.service.chat(self.ta, "What is the latest football score?", "one")
        self.assertTrue(result["handoff"])
        self.assertEqual(result["citations"], [])

    def test_provider_failure_releases_quota(self):
        class Failed:
            def ask(self, *args):
                raise Fault("No key", 503)

        self.service.llm = Failed()
        with self.assertRaises(Fault):
            self.service.chat(self.ta, "books returned", "one", True)
        self.assertEqual(self.service.tenant(self.ta)["used"], 0)

    def test_model_cannot_cite_other_tenant_source(self):
        class Bad:
            def ask(self, *args):
                return {
                    "quotes": [
                        {"source_id": "other-source", "quote": "Other tenant secret"}
                    ]
                }

        self.service.llm = Bad()
        with self.assertRaises(Fault):
            self.service.chat(self.ta, "books returned", "one", True)

    def test_service_recreation_preserves_context(self):
        self.service.chat(self.ta, "books returned", "one")
        reopened = TenantService(self.service.store.database.path)
        self.assertEqual(len(reopened.export(self.ta)["conversations"]), 1)

    def test_concurrent_requests_respect_quota(self):
        tiny = self.service.create_tenant("Tiny", quota=2)

        def attempt(index):
            try:
                self.service.chat(tiny["tenant_token"], "Unknown question", str(index))
                return True
            except Fault:
                return False

        with ThreadPoolExecutor(max_workers=5) as pool:
            results = list(pool.map(attempt, range(5)))
        self.assertEqual(sum(results), 2)
        self.assertEqual(self.service.tenant(tiny["tenant_token"])["used"], 2)

    def test_no_provider_call_for_empty_knowledge(self):
        empty = self.service.create_tenant("Empty")
        result = self.service.chat(empty["tenant_token"], "Question", "one", True)
        self.assertEqual(result["llm_calls"], 0)
        self.assertEqual(result["mode"], "refusal")

    def test_export_omits_token_hash(self):
        self.assertNotIn("token_hash", str(self.service.export(self.ta)))
