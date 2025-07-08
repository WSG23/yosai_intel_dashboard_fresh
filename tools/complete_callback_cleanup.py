"""Utilities to fully remove the deprecated callback controller."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import sys

# Ensure project root is on sys.path when run as a script
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.detect_legacy_callbacks import LegacyCallbackDetector
from tools.migrate_callbacks import migrate_file


def scan_for_legacy_refs(path: Path) -> Dict[str, List[str]]:
    """Return mapping of file -> legacy references found."""
    detector = LegacyCallbackDetector()
    report = detector.scan(path)
    results: Dict[str, List[str]] = {}
    for category in ("imports", "instantiations", "calls"):
        for file, refs in report.get(category, {}).items():
            if refs:
                results.setdefault(file, []).extend(refs)
    return results


def migrate_imports(path: Path) -> int:
    """Rewrite deprecated imports to use ``TrulyUnifiedCallbacks``.

    Returns the number of files modified.
    """
    count = 0
    for py in path.rglob("*.py"):
        if "tests" in py.parts:
            continue
        changed = migrate_file(py, backup=False, show_diff=False)
        if changed:
            count += 1
    return count


def validate_removal(root: Path) -> None:
    """Ensure the legacy controller module is gone and not imported."""
    legacy_file = root / "services" / "data_processing" / "callback_controller.py"
    if legacy_file.exists():
        raise AssertionError(f"Legacy module still present: {legacy_file}")

    bad_imports: List[str] = []
    for py in root.rglob("*.py"):
        if "tests" in py.parts:
            continue
        text = py.read_text(errors="ignore")
        if "services.data_processing.callback_controller" in text:
            bad_imports.append(str(py))
    if bad_imports:
        joined = ", ".join(bad_imports)
        raise AssertionError(f"Legacy imports remain: {joined}")


def test_unified_callbacks() -> None:
    """Basic sanity tests for ``TrulyUnifiedCallbacks``."""
    from dash import Dash, Input, Output

    from core.callback_events import CallbackEvent
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks

    app = Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)

    # Event callbacks
    results: List[int] = []

    def _evt(v: int) -> None:
        results.append(v)

    coord.register_event(CallbackEvent.USER_ACTION, _evt)
    coord.trigger_event(CallbackEvent.USER_ACTION, 5)
    assert results == [5]

    # Dash callbacks
    @coord.register_callback(
        Output("out", "children"),
        Input("in", "value"),
        callback_id="t",
        component_name="test",
    )
    def _cb(v: Any) -> Any:
        return v

    assert _cb("x") == "x"
    assert "t" in coord.registered_callbacks

    # Operations
    coord.register_operation("grp", lambda x: x + 1, name="inc")
    assert coord.execute_group("grp", 1) == [2]


def complete_callback_cleanup(path: Path = Path(".")) -> Dict[str, Any]:
    """Run full cleanup workflow and return a summary."""
    summary: Dict[str, Any] = {}

    legacy = scan_for_legacy_refs(path)
    summary["initial_legacy_refs"] = legacy

    if legacy:
        summary["files_migrated"] = migrate_imports(path)
        legacy = scan_for_legacy_refs(path)
        summary["remaining_legacy_refs"] = legacy

    validate_removal(path)
    test_unified_callbacks()

    summary["status"] = "ok"
    return summary


if __name__ == "__main__":  # pragma: no cover - manual utility
    import json
    report = complete_callback_cleanup()
    print(json.dumps(report, indent=2))
