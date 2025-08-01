from yosai_intel_dashboard.src.services.analytics.storage.persistence import PersistenceManager


class DummyDB:
    pass


def test_initialize(monkeypatch):
    pm = PersistenceManager()
    monkeypatch.setattr(
        "services.helpers.database_initializer.initialize_database",
        lambda *a, **k: (a[0], "helper", "reporter"),
    )
    manager, helper, reporter = pm.initialize(DummyDB())
    assert helper == "helper"
