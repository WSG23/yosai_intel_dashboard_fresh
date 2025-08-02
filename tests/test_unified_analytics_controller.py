import asyncio
import logging

from services.analytics.controllers.unified_controller import UnifiedAnalyticsController


def test_async_security_and_error_logging(caplog):
    controller = UnifiedAnalyticsController()
    results = []

    async def cb(value):
        results.append(value)

    controller.register_callback("on_analysis_start", cb, secure=True)

    with caplog.at_level("ERROR"):
        asyncio.run(
            controller.trigger_async("on_analysis_start", "<script>bad</script>")
        )
    # should not execute callback due to validation failure
    assert results == []
    assert any("Security validation failed" in r.getMessage() for r in caplog.records)
    caplog.clear()

    asyncio.run(controller.trigger_async("on_analysis_start", "hello"))
    assert results == ["hello"]


def test_callback_exception_logging(caplog):
    controller = UnifiedAnalyticsController()

    def bad_cb():
        raise RuntimeError("boom")

    controller.register_callback("on_analysis_complete", bad_cb)

    with caplog.at_level("ERROR"):
        controller.trigger("on_analysis_complete")
    assert any("Callback error" in r.getMessage() for r in caplog.records)
