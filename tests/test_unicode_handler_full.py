import json
import tempfile
from pathlib import Path

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from core.unicode import (
    ChunkedUnicodeProcessor,
    UnicodeProcessor,
    clean_unicode_text,
    safe_decode_bytes,
    safe_encode_text,
    sanitize_dataframe,
)


class CallbackController(TrulyUnifiedCallbacks):
    def fire_event(self, event: CallbackEvent, source_id: str, data=None):
        ctx = type(
            "Ctx", (), {"event_type": event, "source_id": source_id, "data": data or {}}
        )
        self.trigger(event, ctx)

    def register_error_handler(self, handler):
        self._handler = handler

    def trigger(self, event: CallbackEvent, *args, **kwargs):
        try:
            return super().trigger(event, *args, **kwargs)
        except Exception as exc:
            if hasattr(self, "_handler"):
                self._handler(exc, args[0])
            else:
                raise


def callback_handler(event: CallbackEvent):
    def decorator(func):
        _GLOBAL.register_callback(event, func)
        return func

    return decorator


_GLOBAL = CallbackController()
fire_event = _GLOBAL.fire_event
from yosai_intel_dashboard.src.services.data_processing.file_processor import FileProcessor as RobustFileProcessor
from yosai_intel_dashboard.src.services.data_processing.file_processor import (
    process_file_simple,
)


class TestUnicodeProcessor:
    def test_clean_surrogate_chars_basic(self):
        text = "Hello\ud83d\ude00World"
        assert UnicodeProcessor.clean_surrogate_chars(text) == "Hello\U0001f600World"

    def test_clean_surrogate_chars_isolated_surrogates(self):
        text = "Test\ud83dText"
        assert UnicodeProcessor.clean_surrogate_chars(text) == "TestText"
        text = "Test\ude00Text"
        assert UnicodeProcessor.clean_surrogate_chars(text) == "TestText"

    def test_clean_surrogate_chars_with_replacement(self):
        text = "Hello\ud83dWorld"
        assert (
            UnicodeProcessor.clean_surrogate_chars(text, replacement="X")
            == "HelloXWorld"
        )

    def test_safe_decode_bytes_utf8_with_surrogates(self):
        text = "Test\ud83d\ude00Text"
        data = text.encode("utf-8", "surrogatepass")
        result = UnicodeProcessor.safe_decode_bytes(data)
        assert result == "Test\U0001f600Text"

    def test_safe_decode_bytes_fallback_encoding(self):
        text = "Caf\xe9".encode("latin-1")
        assert UnicodeProcessor.safe_decode_bytes(text, "latin-1") == "Café"

    def test_safe_encode_text_various_types(self):
        assert UnicodeProcessor.safe_encode_text("Test\ud83d") == "Test"
        assert UnicodeProcessor.safe_encode_text(None) == ""
        assert UnicodeProcessor.safe_encode_text(pd.NA) == ""
        assert UnicodeProcessor.safe_encode_text(123) == "123"
        assert UnicodeProcessor.safe_encode_text(45.6) == "45.6"
        bytes_val = "hello".encode("utf-8")
        assert UnicodeProcessor.safe_encode_text(bytes_val) == "hello"

    def test_sanitize_dataframe_columns_and_data(self):
        df = pd.DataFrame(
            {"col\ud83d": ["value1\ude00", "value2"], "normal": ["n1", "n2\ud83d"]}
        )
        out = UnicodeProcessor.sanitize_dataframe(df)
        assert "col" in out.columns
        assert "\ud83d" not in str(out.columns)
        assert out.iloc[0, 0] == "value1"
        assert out.iloc[1, 1] == "n2"

    def test_sanitize_dataframe_dangerous_prefixes(self):
        df = pd.DataFrame(
            {"=danger": ["=formula", "+cmd", "-opt", "@imp"], "n": ["a", "b", "c", "d"]}
        )
        out = UnicodeProcessor.sanitize_dataframe(df)
        assert "danger" in out.columns
        assert out.iloc[0, 0] == "formula"
        assert out.iloc[1, 0] == "cmd"
        assert out.iloc[2, 0] == "opt"
        assert out.iloc[3, 0] == "imp"

    def test_sanitize_dataframe_duplicate_columns(self):
        df = pd.DataFrame([[1, 2]], columns=["dup", "dup"])
        out = UnicodeProcessor.sanitize_dataframe(df)
        assert list(out.columns) == ["dup", "dup_1"]

    def test_sanitize_dataframe_empty_columns(self):
        df = pd.DataFrame([[1, 2]], columns=["", None])
        out = UnicodeProcessor.sanitize_dataframe(df)
        assert list(out.columns) == ["col_0", "col_1"]

    def test_sanitize_dataframe_string_dtype(self):
        df = pd.DataFrame({"a": pd.Series(["x\ud800", "y"], dtype="string")})
        out = UnicodeProcessor.sanitize_dataframe(df)
        assert out.loc[0, "a"] == "x"
        assert out["a"].dtype == "string"

    def test_sanitize_dataframe_nested_structures(self):
        df = pd.DataFrame({"col": [["a\ud83d", {"k\ud83d": "v\ude00"}]]})
        out = UnicodeProcessor.sanitize_dataframe(df)
        cell = out.iloc[0, 0]
        assert cell[0] == "a"
        assert "k" in cell[1] and cell[1]["k"] == "v"

    def test_sanitize_dataframe_progress_callback(self):
        df = pd.DataFrame({"c1": ["a"], "c2": ["b"]})
        calls = []

        def cb(i, total):
            calls.append((i, total))

        UnicodeProcessor.sanitize_dataframe(df, progress=cb)
        assert calls and calls[-1] == (2, 2)


class TestChunkedUnicodeProcessor:
    def test_process_large_content_utf8(self):
        content = ("Hello World! " * 1000).encode("utf-8")
        result = ChunkedUnicodeProcessor.process_large_content(content, chunk_size=100)
        assert result == "Hello World! " * 1000

    def test_process_large_content_with_surrogates(self):
        content = ("Test\ud83d\ude00Content" * 500).encode("utf-8", "surrogatepass")
        result = ChunkedUnicodeProcessor.process_large_content(content, chunk_size=50)
        assert result == "Test\U0001f600Content" * 500


class TestCallbackController:
    def test_callback_registration_and_firing(self):
        controller = CallbackController()
        controller._callbacks.clear()
        called = {}

        def cb(ctx):
            called["e"] = ctx.event_type
            called["s"] = ctx.source_id

        controller.register_callback(CallbackEvent.FILE_UPLOAD_START, cb)
        controller.fire_event(CallbackEvent.FILE_UPLOAD_START, "src", {"f": 1})
        assert called["e"] == CallbackEvent.FILE_UPLOAD_START
        assert called["s"] == "src"

    def test_callback_unregistration(self):
        controller = CallbackController()
        controller._callbacks.clear()
        hits = []

        def cb(ctx):
            hits.append(ctx.event_type)

        controller.register_callback(CallbackEvent.ANALYSIS_START, cb)
        controller.fire_event(CallbackEvent.ANALYSIS_START, "t", {})
        assert controller.unregister_callback(CallbackEvent.ANALYSIS_START, cb)
        controller.fire_event(CallbackEvent.ANALYSIS_START, "t", {})
        assert len(hits) == 1

    def test_multiple_callbacks_same_event(self):
        controller = CallbackController()
        controller._callbacks.clear()
        results = []

        def cb1(ctx):
            results.append("cb1")

        def cb2(ctx):
            results.append("cb2")

        controller.register_callback(CallbackEvent.USER_ACTION, cb1)
        controller.register_callback(CallbackEvent.USER_ACTION, cb2)
        controller.fire_event(CallbackEvent.USER_ACTION, "x", {})
        assert results == ["cb1", "cb2"]

    def test_callback_error_handling(self):
        controller = CallbackController()
        controller._callbacks.clear()
        seen = []

        def err_handler(exc, ctx):
            seen.append(str(exc))

        def fail(ctx):
            raise ValueError("boom")

        def ok(ctx):
            seen.append("ok")

        controller.register_error_handler(err_handler)
        controller.register_callback(CallbackEvent.SYSTEM_ERROR, fail)
        controller.register_callback(CallbackEvent.SYSTEM_ERROR, ok)
        controller.fire_event(CallbackEvent.SYSTEM_ERROR, "src", {})
        assert "boom" in seen and "ok" in seen

    def test_callback_decorator(self):
        controller = CallbackController()
        controller._callbacks.clear()
        executed = []

        @callback_handler(CallbackEvent.DATA_QUALITY_CHECK)
        def decorated(ctx):
            executed.append(ctx.source_id)

        controller.fire_event(CallbackEvent.DATA_QUALITY_CHECK, "decor", {})
        assert "decor" in executed


class TestRobustFileProcessor:
    def test_process_csv_basic(self):
        csv = "name,age,city\nJohn,30,NYC\nJane,25,LA".encode("utf-8")
        proc = RobustFileProcessor()
        df, err = proc.process_file(csv, "test.csv")
        assert err is None
        assert len(df) == 2
        assert list(df.columns) == ["name", "age", "city"]

    def test_process_csv_with_unicode_surrogates(self):
        csv = "name\ud83d,value\ntest\ude00,123".encode("utf-8", "surrogatepass")
        proc = RobustFileProcessor()
        df, err = proc.process_file(csv, "u.csv")
        assert err is None
        assert "\ud83d" not in str(df.columns)
        assert "\ude00" not in str(df.values)

    def test_process_csv_different_delimiters(self):
        csv = "name;age;city\nJohn;30;NYC".encode("utf-8")
        proc = RobustFileProcessor()
        df, err = proc.process_file(csv, "semi.csv")
        assert err is None
        assert df.iloc[0]["name"] == "John"

    def test_process_json_basic(self):
        data = json.dumps(
            [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        ).encode("utf-8")
        proc = RobustFileProcessor()
        df, err = proc.process_file(data, "test.json")
        assert err is None and len(df) == 2

    def test_process_json_with_surrogates(self):
        text = json.dumps({"name\ud83d": "val\ude00"})
        proc = RobustFileProcessor()
        df, err = proc.process_file(text.encode("utf-8", "surrogatepass"), "u.json")
        assert err is None
        assert "\ud83d" not in str(df.columns)
        assert "\ude00" not in str(df.values)

    def test_process_excel_basic(self):
        df_original = pd.DataFrame({"name": ["John", "Jane"], "age": [30, 25]})
        with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp:
            df_original.to_excel(tmp.name, index=False)
            excel_bytes = Path(tmp.name).read_bytes()
        proc = RobustFileProcessor()
        df, err = proc.process_file(excel_bytes, "test.xlsx")
        assert err is None and len(df) == 2

    def test_unsupported_file_type(self):
        proc = RobustFileProcessor()
        df, err = proc.process_file(b"content", "test.txt")
        assert err is not None and "Unsupported" in err
        assert df.empty

    def test_empty_file_handling(self):
        proc = RobustFileProcessor()
        df, err = proc.process_file(b"", "test.csv")
        assert err and "empty" in err.lower()

    def test_file_validation_metrics(self):
        df = pd.DataFrame({"col1": ["a", "", "c"], "col2": [1, None, 3]})
        metrics = RobustFileProcessor.validate_dataframe(df)
        assert metrics["valid"] and metrics["rows"] == 3 and metrics["columns"] == 2
        assert "empty_ratio" in metrics and "column_names" in metrics

    def test_callback_integration(self):
        events = []

        def track(ctx):
            events.append(ctx.event_type)

        controller = CallbackController()
        controller._callbacks.clear()
        controller.register_callback(CallbackEvent.FILE_PROCESSING_START, track)
        controller.register_callback(CallbackEvent.FILE_PROCESSING_COMPLETE, track)
        csv = "name,age\nJohn,30".encode("utf-8")
        proc = RobustFileProcessor(controller)
        df, err = proc.process_file(csv, "cb.csv", "src")
        assert err is None and len(df) == 1
        assert CallbackEvent.FILE_PROCESSING_START in events
        assert CallbackEvent.FILE_PROCESSING_COMPLETE in events


class TestPublicAPI:
    def test_clean_unicode_text_function(self):
        assert clean_unicode_text("Hello\ud83dWorld") == "HelloWorld"

    def test_safe_decode_function(self):
        assert safe_decode_bytes(b"Hello") == "Hello"

    def test_safe_encode_function(self):
        assert safe_encode_text("Hello\ud83d") == "Hello"

    def test_sanitize_dataframe_function(self):
        df = pd.DataFrame({"col\ud83d": ["val\ude00"]})
        out = sanitize_dataframe(df)
        assert "col" in out.columns and out.iloc[0, 0] == "val"

    def test_process_file_simple_function(self):
        csv = "name,age\nJohn,30".encode("utf-8")
        df, err = process_file_simple(csv, "simple.csv")
        assert err is None and len(df) == 1


class TestIntegration:
    def test_end_to_end_unicode_file_processing(self):
        content = (
            "name\ud83d,age,city\ude00\n"
            "John\ud83d\ude00,30,NYC\n"
            "=Jane\udfff,25,LA\ud800"
        ).encode("utf-8", "surrogatepass")
        events = []

        def tracker(ctx):
            events.append(ctx.event_type)

        controller = CallbackController()
        controller._callbacks.clear()
        controller.register_callback(CallbackEvent.FILE_PROCESSING_START, tracker)
        controller.register_callback(CallbackEvent.FILE_PROCESSING_COMPLETE, tracker)
        proc = RobustFileProcessor(controller)
        df, err = proc.process_file(content, "complex.csv")
        assert err is None and len(df) == 2
        assert all("\ud83d" not in c and "\ude00" not in c for c in df.columns)
        jane_row = df[df.iloc[:, 0].str.contains("Jane", na=False)]
        assert len(jane_row) == 1 and not jane_row.iloc[0, 0].startswith("=")
        assert CallbackEvent.FILE_PROCESSING_START in events
        assert CallbackEvent.FILE_PROCESSING_COMPLETE in events
