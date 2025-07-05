import gc
import threading

import pytest

from services.data_processing.callback_controller import (
    CallbackController,
    CallbackEvent,
    callback_handler,
    TemporaryCallback,
)


def test_thread_safe_registration():
    controller = CallbackController()
    controller.clear_all_callbacks()
    event = CallbackEvent.FILE_UPLOAD_START
    results = []

    def register(i: int) -> None:
        def cb(ctx):
            results.append(i)
        controller.register_callback(event, cb)

    threads = [threading.Thread(target=register, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    callbacks = controller._registry.get_callbacks(event)
    assert len(callbacks) == 20

    controller.fire_event(event, "src")
    assert sorted(results) == list(range(20))


def test_firing_order_error_isolation_and_stats():
    controller = CallbackController()
    controller.clear_all_callbacks()
    controller.reset_stats()
    event = CallbackEvent.SYSTEM_ERROR
    order = []

    def first(ctx):
        order.append(1)

    def failing(ctx):
        order.append("fail")
        raise RuntimeError("boom")

    def second(ctx):
        order.append(2)

    controller.register_callback(event, first)
    controller.register_callback(event, failing)
    controller.register_callback(event, second)

    controller.fire_event(event, "src")
    assert order == [1, "fail", 2]

    stats = controller.get_stats()
    assert stats["events_fired"] == 1
    assert stats["callbacks_executed"] == 2
    assert stats["errors"] == 1


def test_weak_callback_cleanup():
    controller = CallbackController()
    controller.clear_all_callbacks()
    event = CallbackEvent.USER_ACTION
    called = []

    def make_cb():
        def cb(ctx):
            called.append("called")
        return cb

    cb = make_cb()
    controller.register_callback(event, cb, weak=True)
    assert len(controller._registry.get_callbacks(event)) == 1

    del cb
    gc.collect()

    controller.fire_event(event, "src")
    assert called == []
    assert controller._registry.get_callbacks(event) == []


def test_decorator_and_temporary_callback():
    controller = CallbackController()
    controller.clear_all_callbacks()
    called = []

    @callback_handler(CallbackEvent.UI_UPDATE)
    def decorated(ctx):
        called.append("decorated")

    def temp_cb(ctx):
        called.append("temp")

    with TemporaryCallback(CallbackEvent.UI_UPDATE, temp_cb, controller):
        controller.fire_event(CallbackEvent.UI_UPDATE, "a")
    controller.fire_event(CallbackEvent.UI_UPDATE, "b")

    assert called == ["decorated", "temp", "decorated"]

