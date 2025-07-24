import types
import sys

import pytest

from config import DatabaseConfig
from core.base_database_service import BaseDatabaseService


def _install_fake_module(monkeypatch, name, factory_attr):
    module = types.ModuleType(name)
    conn = object()
    setattr(module, factory_attr, lambda *a, **k: conn)
    monkeypatch.setitem(sys.modules, name, module)
    return conn


def test_postgresql_connection(monkeypatch):
    conn = _install_fake_module(monkeypatch, "psycopg2", "connect")
    service = BaseDatabaseService(DatabaseConfig(type="postgresql"))
    assert service.connection is conn


def test_mysql_connection(monkeypatch):
    conn = _install_fake_module(monkeypatch, "pymysql", "connect")
    service = BaseDatabaseService(DatabaseConfig(type="mysql"))
    assert service.connection is conn


def test_mongodb_connection(monkeypatch):
    module = types.ModuleType("pymongo")
    conn = object()
    module.MongoClient = lambda *a, **k: conn
    monkeypatch.setitem(sys.modules, "pymongo", module)
    service = BaseDatabaseService(DatabaseConfig(type="mongodb"))
    assert service.connection is conn


def test_redis_connection(monkeypatch):
    module = types.ModuleType("redis")
    conn = object()
    module.Redis = lambda *a, **k: conn
    monkeypatch.setitem(sys.modules, "redis", module)
    service = BaseDatabaseService(DatabaseConfig(type="redis"))
    assert service.connection is conn


def test_unsupported_type():
    with pytest.raises(ValueError):
        BaseDatabaseService(DatabaseConfig(type="invalid"))
