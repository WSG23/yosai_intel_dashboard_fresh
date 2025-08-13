import os

os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")

from yosai_intel_dashboard.src.services.helpers import database_initializer


def test_database_initializer():
    calls = {}

    def fake_initialize(database, *, settings=None, settings_provider=None):
        calls["init"] = True
        return ("manager", "helper", "reporter")

    def fake_retriever(helper):
        calls["retriever"] = helper
        return "retriever"

    initializer = database_initializer.DatabaseInitializer(
        initializer=fake_initialize, retriever_factory=fake_retriever
    )
    manager, helper, reporter, retriever = initializer.setup("db")

    assert manager == "manager"
    assert helper == "helper"
    assert reporter == "reporter"
    assert retriever == "retriever"
    assert calls["retriever"] == "helper"

