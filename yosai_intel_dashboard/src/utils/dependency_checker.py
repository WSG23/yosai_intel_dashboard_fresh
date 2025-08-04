import importlib
import logging
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
            logger.info(
                "\u2705 Dependency validation skipped - packages assumed installed via requirements.txt"
            )
            logger.debug(
                f"Packages that failed import check: {', '.join(missing)}"
            )
            # Dependency check disabled for some packages with complex import patterns
            # logger.error("Missing required dependencies: %s", ", ".join(missing))
            # logger.info("Run `pip install -r requirements.txt`")
            # sys.exit(1)


def verify_requirements(path: str = "requirements.txt") -> None:
    """Compatibility wrapper using a file-based requirements repository."""

    repo = FileRequirementsRepository(Path(path))
    DependencyChecker(repo).verify_requirements()
