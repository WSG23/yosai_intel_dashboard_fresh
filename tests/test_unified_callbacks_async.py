import asyncio
import pytest

from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks


class DummyController:
    def __init__(self, order, *, fail=False):
        self.order = order
        self.fail = fail

    async def upload_callbacks(self):
        await asyncio.sleep(0.1)
        self.order.append("upload")
        return [(
            lambda: None,
            "out",
            "in",
            "state",
            "cid_upload",
            {},
        )]

    async def progress_callbacks(self):
        await asyncio.sleep(0.05)
        self.order.append("progress")
        if self.fail:
            raise RuntimeError("boom")
        return []

    async def validation_callbacks(self):
        await asyncio.sleep(0.01)
        self.order.append("validation")
        return []


def test_register_upload_callbacks_concurrent(monkeypatch):
    order: list[str] = []
    controller = DummyController(order)
    registered: list[str] = []
    tuc = TrulyUnifiedCallbacks(security_validator=object())

    def fake_register_handler(outputs, inputs=None, states=None, **kwargs):
        def decorator(func):
            registered.append(kwargs["callback_id"])
            return func
        return decorator

    monkeypatch.setattr(tuc, "register_handler", fake_register_handler)

    asyncio.run(tuc.register_upload_callbacks(controller))

    assert order == ["validation", "progress", "upload"]
    assert registered == ["cid_upload"]


def test_register_upload_callbacks_error(monkeypatch):
    controller = DummyController([], fail=True)
    tuc = TrulyUnifiedCallbacks(security_validator=object())
    monkeypatch.setattr(tuc, "register_handler", lambda *a, **k: (lambda f: f))

    with pytest.raises(RuntimeError):
        asyncio.run(tuc.register_upload_callbacks(controller))
