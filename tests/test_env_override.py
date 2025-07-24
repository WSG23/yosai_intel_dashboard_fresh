import importlib.util
from pathlib import Path
from types import SimpleNamespace, ModuleType

from alembic import context as alembic_context


def load_env_module() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "migrations" / "env.py"
    text = path.read_text()
    idx = text.rfind("\nif context.is_offline_mode():")
    if idx != -1:
        text = text[:idx]
    alembic_context.config = SimpleNamespace(
        config_file_name=str(Path(__file__).resolve().parents[1] / "migrations" / "alembic.ini")
    )
    module = ModuleType("alembic_env")
    exec(compile(text, str(path), "exec"), module.__dict__)
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
