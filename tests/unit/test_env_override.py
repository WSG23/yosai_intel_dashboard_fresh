import importlib.util
import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace

from alembic import context as alembic_context


def load_env_module() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "migrations" / "env.py"
    spec = importlib.util.spec_from_file_location("alembic_env", path)
    module = importlib.util.module_from_spec(spec)
    alembic_context.config = SimpleNamespace(
        config_file_name=str(
            Path(__file__).resolve().parents[1] / "migrations" / "alembic.ini"
        )
    )
    alembic_context.configure = lambda *a, **k: None
    alembic_context.begin_transaction = lambda: SimpleNamespace(
        __enter__=lambda self: None,
        __exit__=lambda self, exc_type, exc, tb: None,
    )
    alembic_context.run_migrations = lambda: None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_env_url_override(monkeypatch):
    env = load_env_module()

    monkeypatch.setattr(env, "_db_sections", lambda: ["gateway_db"])

    captured = {}

    def fake_configure(*args, **kwargs):
        captured["url"] = kwargs.get("url") or (args[0] if args else None)

    class DummyCtx:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(env.context, "configure", fake_configure)
    monkeypatch.setattr(env.context, "begin_transaction", lambda: DummyCtx())
    monkeypatch.setattr(env.context, "run_migrations", lambda: None)

    monkeypatch.setenv("GATEWAY_DB_URL", "postgresql://override/db")
    env.run_migrations_offline()

    assert captured["url"] == "postgresql://override/db"
