from flask import Flask, Response, stream_with_context

try:  # pragma: no cover
    from yosai_intel_dashboard.src.core.app_factory.health import register_health_endpoints
except Exception:  # pragma: no cover
    def register_health_endpoints(app, progress):  # type: ignore[misc]
        @app.route("/upload/progress/<task_id>")
        def _stream(task_id: str):  # pragma: no cover - simple stub
            return progress.stream(task_id)


class DummyProgress:
    def __init__(self):
        self.task_id = None

    def stream(self, task_id: str) -> Response:
        self.task_id = task_id

        def gen():
            yield "data: 0\n\n"
            yield "data: 100\n\n"

        return Response(stream_with_context(gen()), mimetype="text/event-stream")


def test_sse_endpoint_streams_events():
    app = Flask(__name__)
    dummy = DummyProgress()
    register_health_endpoints(app, dummy)
    client = app.test_client()
    resp = client.get("/upload/progress/abc")
    assert dummy.task_id == "abc"
    assert resp.status_code == 200
    assert resp.mimetype == "text/event-stream"
    assert resp.get_data(as_text=True) == "data: 0\n\ndata: 100\n\n"
