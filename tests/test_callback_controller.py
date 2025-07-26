import asyncio

import pytest

from core.callback_controller import CallbackController, CallbackEvent


class TestCallbackController:
    def setup_method(self) -> None:
        self.controller = CallbackController()
        # clear any previously registered callbacks
        self.controller.clear()
        self.controller.reset_stats()

    def test_register_and_fire(self):
        called = []

        def cb(ctx):
            called.append(ctx.data.get("v"))

        self.controller.register(CallbackEvent.ANALYSIS_START, cb)
        self.controller.fire_event(CallbackEvent.ANALYSIS_START, "src", {"v": 1})

        assert called == [1]

    @pytest.mark.asyncio
    async def test_emit_async(self):
        results = []

        async def cb(ctx):
            await asyncio.sleep(0)
            results.append(ctx.source_id)
            return "ok"

        self.controller.register(CallbackEvent.BEFORE_REQUEST, cb)
        out = await self.controller.emit(CallbackEvent.BEFORE_REQUEST, "s")

        assert results == ["s"]
        assert out == ["ok"]
