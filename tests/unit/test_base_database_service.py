import sys
import types

import pytest

from yosai_intel_dashboard.src.core.base_database_service import BaseDatabaseService
from yosai_intel_dashboard.src.core.imports.resolver import safe_import



def _install_fake_module(monkeypatch, name, factory_attr):
    module = types.ModuleType(name)
    conn = object()
    setattr(module, factory_attr, lambda *a, **k: conn)
    monkeypatch.setitem(sys.modules, name, module)
    return conn


def test_postgresql_connection(monkeypatch):
    conn = _install_fake_module(monkeypatch, "psycopg2", "connect")
    service = BaseDatabaseService(
        DatabaseSettings(type="postgresql", user="user", password="pass")
    )
    assert service.connection is conn


def test_mysql_connection(monkeypatch):
    conn = _install_fake_module(monkeypatch, "pymysql", "connect")
    service = BaseDatabaseService(
        DatabaseSettings(type="mysql", user="user", password="pass")
    )
    assert service.connection is conn


def test_mongodb_connection(monkeypatch):
    module = types.ModuleType("pymongo")
    conn = object()
    module.MongoClient = lambda *a, **k: conn
    safe_import('pymongo', module)
    service = BaseDatabaseService(
        DatabaseSettings(type="mongodb", user="user", password="pass")
    )
    assert service.connection is conn


def test_redis_connection(monkeypatch, auto_stub_dependencies):
    module = types.ModuleType("redis")
    conn = object()
    module.Redis = lambda *a, **k: conn
    auto_stub_dependencies("redis", module)
    service = BaseDatabaseService(
        DatabaseSettings(type="redis", user="user", password="pass")
    )
    assert service.connection is conn


def test_unsupported_type():
    with pytest.raises(ValueError):
        BaseDatabaseService(
            DatabaseSettings(type="invalid", user="user", password="pass")
        )
