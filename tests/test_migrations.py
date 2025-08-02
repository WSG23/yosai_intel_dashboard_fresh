import pytest

from services.database.migrations import MigrationManager


class Dummy:
    def __init__(self):
        self.called = []

    def upgrade(self, cfg, rev):
        self.called.append(("upgrade", rev))

    def downgrade(self, cfg, rev):
        self.called.append(("downgrade", rev))

    def current(self, cfg):
        self.called.append(("current", None))


@pytest.fixture
def monkeypatched_commands(monkeypatch):
    dummy = Dummy()
    monkeypatch.setattr("alembic.command.upgrade", dummy.upgrade)
    monkeypatch.setattr("alembic.command.downgrade", dummy.downgrade)
    monkeypatch.setattr("alembic.command.current", dummy.current)
    return dummy


def test_migration_upgrade_and_rollback(monkeypatched_commands):
    mgr = MigrationManager("alembic.ini")
    mgr.upgrade("head")
    assert ("upgrade", "head") in monkeypatched_commands.called
    mgr.rollback()
    # rollback triggers downgrade
    assert ("downgrade", "base") in monkeypatched_commands.called


def test_cli_current(monkeypatched_commands):
    from scripts import db_migration_cli

    exit_code = db_migration_cli.main(
        [
            "--config",
            "migrations/alembic.ini",
            "current",
        ]
    )

    assert exit_code == 0
    assert ("current", None) in monkeypatched_commands.called
