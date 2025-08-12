import importlib
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List

from ..repository.requirements import (
    FileRequirementsRepository,
    RequirementsRepository,
)

logger = logging.getLogger(__name__)

# Map pip package names to their corresponding Python import names. This ensures
# that dependency checks use the correct module names even when they differ from
# the package identifier used in ``requirements.txt``.
PACKAGE_MODULE_MAP: Dict[str, str] = {
    "flask-babel": "flask_babel",
    "flask-caching": "flask_caching",
    "flask-compress": "flask_compress",
    "flask-login": "flask_login",
    "flask-wtf": "flask_wtf",
    "psycopg2-binary": "psycopg2",
    "python-dotenv": "dotenv",
    "python-jose": "jose",
    "scikit-learn": "sklearn",
    "pyyaml": "yaml",
}


def check_dependencies(packages: Iterable[str]) -> List[str]:
    missing = []
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


class DependencyChecker:
    """Validate that listed packages are importable."""

    def __init__(self, repo: RequirementsRepository) -> None:
        self._repo = repo

    def verify_requirements(self) -> None:
        packages = [
            PACKAGE_MODULE_MAP.get(pkg.lower(), pkg.lower().replace("-", "_"))
            for pkg in self._repo.get_packages()
        ]
        missing = check_dependencies(packages)
        if missing:
            raise RuntimeError(
                f"Missing required dependencies: {', '.join(sorted(missing))}"
            )


def verify_requirements(path: str = "requirements.txt") -> None:
    """Compatibility wrapper using a file-based requirements repository.

    Raises
    ------
    RuntimeError
        If any required dependency is missing or a requirement is not pinned.
    """

    repo = FileRequirementsRepository(Path(path))
    unpinned = repo.get_unpinned_packages()
    if unpinned:
        raise RuntimeError(
            "Unpinned dependencies detected: " + ", ".join(sorted(unpinned))
        )

    DependencyChecker(repo).verify_requirements()
    vulnerabilities = _scan_vulnerabilities()
    if vulnerabilities:
        raise RuntimeError(
            "High severity vulnerabilities detected: " + ", ".join(vulnerabilities)
        )


def _scan_vulnerabilities() -> List[str]:
    """Run ``pip-audit`` and return any high or critical findings."""

    try:
        result = subprocess.run(
            ["pip-audit", "-f", "json"],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        logger.warning("pip-audit not installed; skipping vulnerability scan")
        return []

    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        logger.warning("Failed to parse pip-audit output: %s", result.stdout)
        return []

    findings = [
        f"{entry.get('name')} {entry.get('version')}: {vuln.get('id')}"
        for entry in data
        for vuln in entry.get("vulns", [])
        if (vuln.get("severity") or "").lower() in {"high", "critical"}
    ]
    return findings


if __name__ == "__main__":
    verify_requirements()
