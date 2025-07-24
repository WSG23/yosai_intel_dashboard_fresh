import sys
import types
from pathlib import Path

# Ensure project root on path for imports
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Prevent importing the real analytics package during collection
ANALYTICS_DIR = Path(__file__).resolve().parents[1]
if "analytics" not in sys.modules:
    analytics_stub = types.ModuleType("analytics")
    analytics_stub.__path__ = [str(ANALYTICS_DIR)]
    sys.modules["analytics"] = analytics_stub
if "analytics.anomaly_detection" not in sys.modules:
    ad_stub = types.ModuleType("analytics.anomaly_detection")
    ad_stub.__path__ = [str(ANALYTICS_DIR / "anomaly_detection")]
    sys.modules["analytics.anomaly_detection"] = ad_stub

# Minimal stubs for optional dependencies used when importing the analytics package
sys.modules.setdefault("redis", types.ModuleType("redis"))
sys.modules.setdefault("redis.asyncio", types.ModuleType("redis.asyncio"))

flask_stub = types.ModuleType("flask")
flask_stub.request = object()
flask_stub.url_for = lambda *a, **k: ""
sys.modules.setdefault("flask", flask_stub)

hvac_stub = types.ModuleType("hvac")
hvac_stub.Client = object
sys.modules.setdefault("hvac", hvac_stub)

crypto_stub = types.ModuleType("cryptography")
fernet_stub = types.ModuleType("cryptography.fernet")
class DummyFernet:
    def __init__(self, *args, **kwargs): ...
    def encrypt(self, data: bytes) -> bytes: return data
    def decrypt(self, data: bytes) -> bytes: return data
    @staticmethod
    def generate_key() -> bytes: return b""
fernet_stub.Fernet = DummyFernet
crypto_stub.fernet = fernet_stub
sys.modules.setdefault("cryptography", crypto_stub)
sys.modules.setdefault("cryptography.fernet", fernet_stub)

# Minimal opentelemetry stub
otel_stub = types.ModuleType("opentelemetry")
otel_trace = types.ModuleType("opentelemetry.trace")
otel_stub.trace = otel_trace
sys.modules.setdefault("opentelemetry", otel_stub)
sys.modules.setdefault("opentelemetry.trace", otel_trace)

# Dash stubs
from tests.stubs import dash as dash_stub

sys.modules.setdefault("dash", dash_stub)
sys.modules.setdefault("dash.dependencies", dash_stub.dependencies)
dash_stub.no_update = object()
