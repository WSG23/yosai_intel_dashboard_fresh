import importlib
import logging
from pathlib import Path
from typing import Iterable, List

logger = logging.getLogger(__name__)


def check_dependencies(packages: Iterable[str]) -> List[str]:
    missing = []
    for pkg in packages:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


def verify_requirements(path: str = "requirements.txt") -> None:
    reqs: List[str] = []
    with open(Path(path), "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                reqs.append(line.split("==")[0].split(">=")[0].split("~=")[0])
    missing = check_dependencies(reqs)
    if missing:
        logger.error("Missing required dependencies: %s", ", ".join(sorted(missing)))
        logger.info("Run `pip install -r %s`", path)
        raise SystemExit(1)
