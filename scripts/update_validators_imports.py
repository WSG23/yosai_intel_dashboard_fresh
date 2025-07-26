#!/usr/bin/env python3
"""Rewrite deprecated validator imports.

This helper updates imports of legacy validation classes to use the new
centralized ``validation`` package. Run without ``--write`` to preview
changes.

Example (dry run)::

    python scripts/update_validators_imports.py path/to/package

Apply modifications in place::

    python scripts/update_validators_imports.py --write src tests
"""
from __future__ import annotations

import argparse
from bowler import Query
from fissix.fixer_util import Name
from lib2to3.pgen2 import token

MODULE_REPLACEMENTS = {
    "services.data_processing.unified_upload_validator": "validation.security_validator",
    "services.data_processing.unified_file_validator": "validation.security_validator",
    "services.input_validator": "validation.security_validator",
    "upload_validator": "validation.security_validator",
    "core.security_validator": "validation.security_validator",
}

NAME_REPLACEMENTS = {
    "UnifiedUploadValidator": "SecurityValidator",
    "UnifiedFileValidator": "SecurityValidator",
    "InputValidator": "SecurityValidator",
    "UploadValidator": "SecurityValidator",
}


def make_callback(new_module: str):
    def _callback(node, capture, filename):
        if "module_name" in capture:
            capture["module_name"].replace(
                Name(new_module, prefix=capture["module_name"].prefix)
            )
        if "module_import" in capture:
            old = capture["module_import"].value
            new = NAME_REPLACEMENTS.get(old, old)
            if new != old:
                capture["module_import"].value = new
                capture["module_import"].changed()
        if "module_imports" in capture:
            for leaf in capture["module_imports"]:
                if leaf.type == token.NAME:
                    new = NAME_REPLACEMENTS.get(leaf.value, leaf.value)
                    if new != leaf.value:
                        leaf.value = new
                        leaf.changed()

    return _callback


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Update deprecated validator imports to new modules"
    )
    parser.add_argument("paths", nargs="+", help="Files or directories to refactor")
    parser.add_argument(
        "--write", action="store_true", help="Modify files in place instead of preview"
    )
    args = parser.parse_args(argv)

    query = Query(args.paths)
    for old_module, new_module in MODULE_REPLACEMENTS.items():
        query = query.select_module(old_module).modify(make_callback(new_module))
    query.execute(write=args.write, interactive=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
