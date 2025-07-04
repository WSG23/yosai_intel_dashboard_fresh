from callback_controller import CallbackController, CallbackEvent
from robust_file_processor import RobustFileProcessor


def test_unicode_processing_and_events():
    csv = "name\uD83D,value\ntest\uDE00,1".encode("utf-8", "surrogatepass")
    controller = CallbackController()
    events = []

    def track(ctx):
        events.append(ctx.event_type)

    controller.clear_all_callbacks()
    controller.register_callback(CallbackEvent.FILE_PROCESSING_START, track)
    controller.register_callback(CallbackEvent.FILE_PROCESSING_COMPLETE, track)

    proc = RobustFileProcessor(controller)
    df, err = proc.process_file(csv, "test.csv", "src")
    assert err is None
    assert CallbackEvent.FILE_PROCESSING_START in events
    assert CallbackEvent.FILE_PROCESSING_COMPLETE in events
    assert "\uD83D" not in str(df.columns[0])
    assert "\uDE00" not in str(df.iloc[0, 0])
