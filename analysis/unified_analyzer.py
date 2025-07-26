import ast
import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Set


class UnifiedAnalyzer:
    """Unified analyzer supporting Python and multi-language projects."""

    def __init__(
        self,
        project_path: str,
        languages: Optional[List[str]] = None,
        exclude_dirs: Optional[Set[str]] = None,
    ) -> None:
        self.project_path = Path(project_path)
        self.languages = languages or ["python"]
        self.exclude_dirs = exclude_dirs or {
            ".git",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            "venv",
            "env",
            ".venv",
            "dist",
            "build",
            ".next",
            ".idea",
            ".vscode",
            "coverage",
            "htmlcov",
            "vendor",
        }
        self.issues: Dict[str, List[str]] = defaultdict(list)

    # ------------------------------------------------------------------
    # helpers
    def _iter_files(self, extensions: List[str]) -> List[Path]:
        files = []
        for ext in extensions:
            for fpath in self.project_path.rglob(f"*{ext}"):
                if any(ex in fpath.parts for ex in self.exclude_dirs):
                    continue
                files.append(fpath)
        return files

    # ------------------------------------------------------------------
    # multi-language overview
    def _scan_files(self) -> Dict:
        stats = {"total_files": 0, "files_by_type": defaultdict(list)}
        ext_to_lang = {
            ".py": "Python",
            ".go": "Go",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JavaScript",
            ".tsx": "TypeScript",
        }
        for p in self.project_path.rglob("*"):
            if p.is_file():
                if any(ex in p.parts for ex in self.exclude_dirs):
                    continue
                stats["total_files"] += 1
                lang = ext_to_lang.get(p.suffix.lower())
                if lang:
                    stats["files_by_type"][lang].append(p)
        return stats

    # ------------------------------------------------------------------
    # python analysis
    def _analyze_python(self) -> Dict:
        duplicates = defaultdict(list)
        signatures = defaultdict(list)
        unicode_issues = []
        py_files = self._iter_files([".py"])
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        sig = f"{node.name}({','.join(arg.arg for arg in node.args.args)})"
                        signatures[sig].append(
                            {
                                "file": str(py_file.relative_to(self.project_path)),
                                "line": node.lineno,
                            }
                        )
                for match in re.finditer(r"\.encode\(\)|\.decode\(\)", content):
                    line_no = content[: match.start()].count("\n") + 1
                    unicode_issues.append(
                        {
                            "file": str(py_file.relative_to(self.project_path)),
                            "line": line_no,
                        }
                    )
            except Exception as exc:
                self.issues["parse_errors"].append(f"{py_file}: {exc}")
        for sig, locs in signatures.items():
            if len(locs) > 1:
                duplicates[sig] = locs
        return {
            "files_analyzed": len(py_files),
            "duplicate_functions": len(duplicates),
            "unicode_issues": unicode_issues,
        }

    # ------------------------------------------------------------------
    # basic security scan across languages
    def _security_scan(self, files_by_type: Dict[str, List[Path]]) -> Dict:
        issues = defaultdict(list)
        pattern = r'(?i)(password|secret|token)\s*[:=]\s*["\']'
        for lang, files in files_by_type.items():
            for fpath in files[:50]:
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                    for match in re.finditer(pattern, content):
                        line_no = content[: match.start()].count("\n") + 1
                        issues[lang].append(
                            {
                                "file": str(fpath.relative_to(self.project_path)),
                                "line": line_no,
                            }
                        )
                except Exception:
                    continue
        total = sum(len(v) for v in issues.values())
        return {"issues": dict(issues), "total": total}

    # ------------------------------------------------------------------
    def analyze(self) -> Dict:
        results = {"structure": self._scan_files()}
        if "python" in [l.lower() for l in self.languages]:
            results["python"] = self._analyze_python()
        if len(self.languages) > 1:
            results["multilanguage_security"] = self._security_scan(
                results["structure"]["files_by_type"]
            )
        return results

    def generate_report(self, results: Dict) -> str:
        lines = [
            f"Project: {self.project_path}",
            f"Total files: {results['structure']['total_files']}",
        ]
        if "python" in results:
            py = results["python"]
            lines.append(f"Python files analyzed: {py['files_analyzed']}")
            lines.append(f"Duplicate functions: {py['duplicate_functions']}")
            lines.append(f"Unicode issues: {len(py['unicode_issues'])}")
        if "multilanguage_security" in results:
            sec = results["multilanguage_security"]
            lines.append(f"Security issues across languages: {sec['total']}")
        return "\n".join(lines)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Unified code analyzer")
    parser.add_argument("project_path")
    parser.add_argument(
        "--languages",
        default="python",
        help="Comma separated languages to analyze (e.g. python,js)",
    )
    parser.add_argument("--output", help="Optional JSON output file")
    args = parser.parse_args()
    langs = [l.strip() for l in args.languages.split(",") if l.strip()]
    analyzer = UnifiedAnalyzer(args.project_path, languages=langs)
    results = analyzer.analyze()
    print(analyzer.generate_report(results))
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)


if __name__ == "__main__":
    main()
