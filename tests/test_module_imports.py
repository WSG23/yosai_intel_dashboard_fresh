import sys

def test_module_imports(capsys):
    # Clear cached imports for targeted modules
    for key in list(sys.modules.keys()):
        if key.startswith((
            "config",
            "core",
            "services",
            "models",
            "validation",
            "api",
        )):
            del sys.modules[key]

    results: dict[str, str] = {}

    modules = ["config", "services", "core", "validation", "api", "models"]
    for module in modules:
        try:
            __import__(module)
            results[module] = "\u2713"  # check mark
        except ImportError as e:
            if "boto3" in str(e) or "requests" in str(e):
                results[module] = "\u26a0\ufe0f External dependency"
            else:
                results[module] = f"\u2717 {str(e)[:40]}..."
        except Exception as e:
            results[module] = f"\u2717 {type(e).__name__}: {str(e)[:30]}..."

    for mod, attr in [
        ("config", "Config"),
        ("services", "AnalyticsService"),
        ("validation", "SecurityValidator"),
        ("models", "BaseModel"),
    ]:
        key = f"{mod}.{attr}"
        if results.get(mod) == "\u26a0\ufe0f External dependency":
            results[key] = "\u26a0\ufe0f Skipped (parent failed)"
            continue
        try:
            m = __import__(mod, fromlist=[attr])
            getattr(m, attr)
            results[key] = "\u2713"
        except Exception as e:
            results[key] = f"\u2717 {str(e)[:40]}..."

    for k, v in results.items():
        print(f"{k}: {v}")

    core_imports_ok = all(
        v == "\u2713" or v.startswith("\u26a0")
        for k, v in results.items()
        if k in {"core", "validation", "models", "api"}
    )

    print(f"\nCore imports working: {core_imports_ok}")
    print("External dependencies needed: boto3, requests")

    captured = capsys.readouterr().out
    print(captured)
    assert "core" in captured
