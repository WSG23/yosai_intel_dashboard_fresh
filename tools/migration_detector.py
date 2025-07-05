"""Automated detection of legacy Unicode utilities"""
from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


class MigrationDetector:
    """Scan codebase for deprecated Unicode helpers and generate migration reports."""

    LEGACY_PATTERNS = {
        'utils.unicode_utils.sanitize_unicode_input': 'core.unicode.UnicodeSecurityProcessor.sanitize_input',
        'utils.unicode_utils.clean_unicode_text': 'core.unicode.UnicodeTextProcessor.clean_text',
        'utils.unicode_utils.sanitize_dataframe': 'core.unicode.sanitize_dataframe',
        'config.unicode_handler.safe_encode_query': 'core.unicode.UnicodeSQLProcessor.encode_query',
        'security.unicode_security_handler.sanitize_dataframe': 'core.unicode.sanitize_dataframe',
    }

    def __init__(self) -> None:
        self.usage: Dict[str, List[str]] = defaultdict(list)

    # ------------------------------------------------------------------
    def scan_codebase(self, directory: str) -> Dict[str, List[str]]:
        """Scan ``directory`` for legacy Unicode function usage."""
        for path in Path(directory).rglob('*.py'):
            try:
                tree = ast.parse(path.read_text())
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        full = f"{module}.{alias.name}"
                        if full in self.LEGACY_PATTERNS:
                            self.usage[full].append(str(path))
                elif isinstance(node, ast.Attribute):
                    full = f"{getattr(node.value, 'id', '')}.{node.attr}"
                    if full in self.LEGACY_PATTERNS:
                        self.usage[full].append(str(path))
        return self.usage

    # ------------------------------------------------------------------
    def generate_migration_script(self, file_path: str) -> str:
        """Return migration script suggestions for ``file_path``."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(file_path)
        text = path.read_text()
        for legacy, new in self.LEGACY_PATTERNS.items():
            module, func = legacy.rsplit('.', 1)
            if f"{func}" in text and module in text:
                text = text.replace(legacy.split('.')[-1], new.split('.')[-1])
                text = text.replace(module, new.rsplit('.', 1)[0])
        return text

    # ------------------------------------------------------------------
    def validate_migration(self, original_file: str, migrated_file: str) -> bool:
        """Validate that migration preserves functionality (placeholder)."""
        return Path(migrated_file).exists()

    # ------------------------------------------------------------------
    def create_migration_report(self) -> Dict[str, Any]:
        """Return a migration report summarizing detected legacy usage."""
        return {"usage": self.usage, "total": sum(len(v) for v in self.usage.values())}


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Detect Unicode migration needs")
    parser.add_argument('--scan', metavar='DIR', help='directory to scan')
    parser.add_argument('--output', help='write report to file')
    args = parser.parse_args()

    det = MigrationDetector()
    report = det.scan_codebase(args.scan or '.')
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))

