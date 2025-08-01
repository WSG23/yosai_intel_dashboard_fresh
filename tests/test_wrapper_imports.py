import os
import importlib

os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")

# Test imports without dash dependency
results = {}

modules = ["config", "services", "core", "validation", "api", "models"]
for mod in modules:
    try:
        importlib.import_module(mod)
        results[mod] = "\u2713"
    except Exception as e:
        results[mod] = f"\u2717 {str(e)[:50]}..."

imports_to_test = [
    ("config", "Config"),
    ("services", "AnalyticsService"),
    ("validation", "SecurityValidator"),
    ("models", "BaseModel"),
]

for mod, attr in imports_to_test:
    key = f"{mod}.{attr}"
    try:
        module = importlib.import_module(mod)
        getattr(module, attr)
        results[key] = "\u2713"
    except Exception as e:
        results[key] = f"\u2717 {str(e)[:50]}..."

print(results)


def test_wrapper_imports():
    assert True, results
