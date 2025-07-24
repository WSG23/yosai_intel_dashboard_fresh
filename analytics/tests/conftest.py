import sys
import types
from pathlib import Path

# Ensure project root on path for imports
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Prevent importing the real analytics package during collection
ANALYTICS_DIR = Path(__file__).resolve().parents[1]
if "analytics" not in sys.modules:
    analytics_stub = types.ModuleType("analytics")
    analytics_stub.__path__ = [str(ANALYTICS_DIR)]
    sys.modules["analytics"] = analytics_stub

# Minimal stubs for optional dependencies
sys.modules.setdefault("redis", types.ModuleType("redis"))
sys.modules.setdefault("redis.asyncio", types.ModuleType("redis.asyncio"))
