import pathlib
import sys
import types

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2]

# Provide a lightweight 'services' package to avoid heavy dependencies during test collection
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)
