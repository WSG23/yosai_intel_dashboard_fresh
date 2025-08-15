import importlib
from types import SimpleNamespace

import alembic.context

import yosai_intel_dashboard.src.infrastructure.configparser


class DummyConnection:
    def __init__(self, dialect_name="sqlite"):
        self.dialect = type("dialect", (), {"name": dialect_name})()

    def connect(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def execute(self, *a, **k):
        pass


class DummyEngine(DummyConnection):
    pass


def test_skip_timescale_for_sqlite(monkeypatch, tmp_path):
    cfg_file = tmp_path / "alembic.ini"
    cfg_file.write_text("[foo_db]\nsqlalchemy.url = sqlite://\n")
    alembic.context.config = SimpleNamespace(config_file_name=str(cfg_file))
    alembic.context.is_offline_mode = lambda: True
    alembic.context.configure = lambda **kw: None

    class DummyTxn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    alembic.context.begin_transaction = lambda: DummyTxn()
    alembic.context.run_migrations = lambda: None
    monkeypatch.setattr("logging.config.fileConfig", lambda *a, **k: None)
    env = importlib.import_module("migrations.env")
    calls = []
    monkeypatch.setattr(env, "_ensure_timescale", lambda conn: calls.append(True))

    def fake_engine_from_config(opts, prefix="sqlalchemy.", poolclass=None):
        return DummyEngine()

    monkeypatch.setattr(env, "engine_from_config", fake_engine_from_config)
    monkeypatch.setattr(env.context, "configure", lambda **kw: None)
    monkeypatch.setattr(env.context, "run_migrations", lambda: None)

    class DummyTxn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(env.context, "begin_transaction", lambda: DummyTxn())

    parser = configparser.ConfigParser()
    parser.read_dict({"foo_db": {"sqlalchemy.url": "sqlite://"}})
    env.parser = parser

    env.run_migrations_online()
    assert not calls
