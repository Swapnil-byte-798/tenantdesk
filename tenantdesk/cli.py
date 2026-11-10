from pathlib import Path
import tempfile
from .runtime import run_cli, settings
from .service import TenantService


def demo():
    with tempfile.TemporaryDirectory() as directory:
        service = TenantService(Path(directory) / "demo.db")
        first = service.create_tenant("Example Books")
        second = service.create_tenant("Example Hardware")
        service.put_document(
            first["tenant_token"],
            "returns",
            "Returns",
            "Books can be returned within fourteen days of delivery.",
        )
        service.put_document(
            second["tenant_token"],
            "returns",
            "Returns",
            "Tools can be returned within thirty days of delivery.",
        )
        return {
            "data": "two authored tenant fixtures",
            "first": service.chat(
                first["tenant_token"], "When can books be returned?", "one"
            ),
            "second": service.chat(
                second["tenant_token"], "When can tools be returned?", "one"
            ),
        }


def extend(sub):
    command = sub.add_parser("init-postgres")

    def initialize(args):
        from .postgres import PostgresStore

        config = settings()
        PostgresStore(
            config.get("TENANTDESK_DATABASE_URL", ""),
            config.get("TENANTDESK_ADMIN_DATABASE_URL", ""),
        ).initialize()
        return {
            "initialized": True,
            "runtime_role": "tenantdesk_runtime",
            "forced_rls": True,
        }

    command.set_defaults(action=initialize)


def main():
    run_cli("tenantdesk", demo, ("GROQ_API_KEY",), extend)
