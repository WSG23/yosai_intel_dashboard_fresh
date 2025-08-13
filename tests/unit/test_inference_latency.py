import ast
import time
from pathlib import Path
from types import SimpleNamespace

def test_run_prediction_emits_latency():
    path = (
        Path(__file__).resolve().parents[2]
        / "yosai_intel_dashboard"
        / "src"
        / "services"
        / "analytics_microservice"
        / "app.py"
    )
    source = path.read_text()
    module_ast = ast.parse(source)
    run_node = next(
        n for n in module_ast.body if isinstance(n, ast.FunctionDef) and n.name == "_run_prediction"
    )
    ast.fix_missing_locations(run_node)
    mod = ast.Module(body=[run_node], type_ignores=[])
    code = compile(mod, str(path), "exec")
    calls: list[tuple[str, float]] = []
    env = {
        "perf_counter": time.perf_counter,
        "http_error": lambda *a, **k: None,
        "ErrorCode": SimpleNamespace(INTERNAL="INTERNAL"),
        "_INFERENCE_LATENCY": SimpleNamespace(
            labels=lambda m: SimpleNamespace(observe=lambda v: calls.append((m, v)))
        ),
        "logger": SimpleNamespace(debug=lambda *a, **k: None),
        "Any": object,
    }
    exec(code, env)
    run_prediction = env["_run_prediction"]

    class Model:
        def predict(self, data):
            return data

    result, latency = run_prediction(Model(), [1])
    assert result == [1]
    assert latency >= 0
    assert calls and calls[0][1] == latency
