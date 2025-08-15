class DummyConn:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_close_resets_connection() -> None:
    from analytics.context_storage import TimescaleContextStore

    store = TimescaleContextStore("dsn")
    store._conn = DummyConn()
    store.close()
    assert store._conn is None
    assert store._conn is None or getattr(store._conn, "closed", True)


def test_context_manager_closes() -> None:
    from analytics.context_storage import TimescaleContextStore

    store = TimescaleContextStore("dsn")
    store._conn = DummyConn()
    with store:
        pass
    assert store._conn is None
