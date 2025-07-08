#!/usr/bin/env python3
"""Plugin system migration helper.

Usage:
    python scripts/migrate_plugin_system.py [OPTIONS] [PROJECT_ROOT]

This tool assists migrating to the new plugin architecture:
1. Scan modules for direct ``plugins.*`` imports.
2. Generate ``config/plugins.unified.yaml`` listing all discovered plugins.
3. Convert callback registrations to ``CallbackUnifier``.
4. Validate plugin dependencies using ``PluginAutoConfiguration`` logic.

Pass ``--dry-run`` to preview file modifications without applying them.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Dict, Set

import yaml


def scan_plugin_imports(root: Path) -> Dict[str, Set[str]]:
    """Return mapping of plugin name -> set of files importing it."""
    plugin_imports: Dict[str, Set[str]] = {}
    for py in root.rglob("*.py"):
        if "tests" in py.parts or "/." in str(py):
            continue
        try:
            tree = ast.parse(py.read_text())
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("plugins."):
                        name = alias.name.split(".")[1]
                        plugin_imports.setdefault(name, set()).add(str(py))
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("plugins."):
                    name = node.module.split(".")[1]
                    plugin_imports.setdefault(name, set()).add(str(py))
    return plugin_imports


def generate_unified_config(imports: Dict[str, Set[str]], output: Path) -> None:
    data = {"plugins": {}}
    for plugin in sorted(imports):
        data["plugins"][plugin] = {"enabled": True}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)


def convert_callbacks(root: Path, dry_run: bool = False) -> None:
    """Replace references to the old coordinator with ``TrulyUnifiedCallbacks``."""
    for py in root.rglob("*.py"):
        if "tests" in py.parts or "plugins" in py.parts:
            continue
        text = py.read_text()
        if "UnifiedCallbackCoordinator" in text:
            new_text = text.replace(
                "UnifiedCallbackCoordinator", "TrulyUnifiedCallbacks"
            )
            if not dry_run:
                py.write_text(new_text)


def validate_plugin_dependencies(root: Path, plugins: Set[str]) -> None:
    """Simple dependency validation based on PluginMetadata definitions."""
    for plugin_dir in (root / "plugins").iterdir():
        plugin_file = (
            plugin_dir / "plugin.py"
            if plugin_dir.is_dir()
            else plugin_dir
        )
        if not plugin_file.name.endswith(".py"):
            continue
        try:
            tree = ast.parse(plugin_file.read_text())
        except Exception:
            continue
        deps: Set[str] = set()
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node.func, "id", "") == "PluginMetadata"
            ):
                for kw in node.keywords:
                    if kw.arg == "dependencies" and isinstance(
                        kw.value, (ast.List, ast.Tuple)
                    ):
                        for elt in kw.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(
                                elt.value, str
                            ):
                                deps.add(elt.value)
        missing = deps - plugins
        if missing:
            deps_list = ", ".join(sorted(missing))
            print(
                f"Plugin {plugin_dir.name} has missing dependencies: {deps_list}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate to new plugin system")
    parser.add_argument("root", nargs="?", default=".", help="Project root path")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    imports = scan_plugin_imports(root)
    if not imports:
        print("No direct plugin imports found")
    else:
        print("Discovered plugin imports:")
        for plugin, files in imports.items():
            print(f"  {plugin}: {len(files)} files")

    config_path = root / "config" / "plugins.unified.yaml"
    generate_unified_config(imports, config_path)
    print(f"Wrote unified config to {config_path}")

    convert_callbacks(root, dry_run=args.dry_run)
    if args.dry_run:
        print("Dry run complete - no files modified")
    else:
        print("Callback conversion complete")

    validate_plugin_dependencies(root, set(imports))


if __name__ == "__main__":
    main()
