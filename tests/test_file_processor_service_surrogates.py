import importlib.util
import sys
import types
import os
from pathlib import Path

from core.unicode import sanitize_unicode_input


def load_service():
    root = Path(__file__).resolve().parents[1]
    # Stub heavy dependencies to avoid loading optional packages
    class DummyCache:
        def __init__(self, *a, **k):
            pass

        def memoize(self, *a, **k):
            def dec(f):
                return f

            return dec

        def __call__(self, *a, **k):
            return None

        def init_app(self, *a, **k):
            pass

    stubs = {
        "dash": types.ModuleType("dash"),
        "dash.html": types.ModuleType("dash.html"),
        "bleach": types.ModuleType("bleach"),
        "sqlparse": types.ModuleType("sqlparse"),
        "flask_caching": types.ModuleType("flask_caching"),
        "flask": types.ModuleType("flask"),
        "flask_babel": types.ModuleType("flask_babel"),
        "flask_login": types.ModuleType("flask_login"),
        "flask_wtf": types.ModuleType("flask_wtf"),
        "flask_compress": types.ModuleType("flask_compress"),
        "flask_talisman": types.ModuleType("flask_talisman"),
        "psycopg2": types.ModuleType("psycopg2"),
        "psycopg2_binary": types.ModuleType("psycopg2_binary"),
        "requests": types.ModuleType("requests"),
        "sqlalchemy": types.ModuleType("sqlalchemy"),
        "psutil": types.ModuleType("psutil"),
        "utils.file_validator": types.ModuleType("utils.file_validator"),
    }
    stubs["flask_caching"].Cache = DummyCache
    stubs["sqlparse"].tokens = types.SimpleNamespace()
    stubs["dash"].html = types.ModuleType("html")
    stubs["flask"].Flask = object
    stubs["utils.file_validator"].safe_decode_with_unicode_handling = (
        lambda d, e: d.decode(e, "ignore")
    )

    for name, mod in stubs.items():
        sys.modules.setdefault(name, mod)

    import core.unicode as cu
    from core.unicode_decode import safe_unicode_decode

    cu.safe_unicode_decode = safe_unicode_decode

    services_pkg = types.ModuleType("services")
    services_pkg.__path__ = [str(root / "services")]
    sys.modules["services"] = services_pkg

    spec = importlib.util.spec_from_file_location(
        "services.file_processor_service", str(root / "services" / "file_processor_service.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.FileProcessorService()


def test_decode_with_surrogate_pairs():
    svc = load_service()
    data = "col\nval\ud83d\ude00".encode("utf-8", "surrogatepass")
    text = svc._decode_with_surrogate_handling(data, "utf-8")
    assert "val" in text
    assert "\ud83d" not in text
    assert "\ude00" not in text
