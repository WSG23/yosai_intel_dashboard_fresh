import os
import subprocess

def _get_base_ref() -> str:
    base_env = os.environ.get("BASE_BRANCH")
    refs = [base_env] if base_env else []
    refs += ["origin/main", "origin/master", "main", "master"]
    for ref in refs:
        if not ref:
            continue
        try:
            return subprocess.check_output(["git", "merge-base", "HEAD", ref]).strip().decode()
        except subprocess.CalledProcessError:
            continue
    return subprocess.check_output(["git", "rev-list", "--max-parents=0", "HEAD"]).strip().decode()

def _changed_files() -> list[str]:
    base = _get_base_ref()
    output = subprocess.check_output(["git", "diff", "--name-only", base, "HEAD"])
    return output.decode().splitlines()

def test_architecture_diagram_updated() -> None:
    changed = _changed_files()
    relevant = [
        f for f in changed
        if f.startswith("shared/events")
        or f.startswith("yosai_intel_dashboard/src/infrastructure/callbacks")
    ]
    if relevant and "docs/architecture.md" not in changed:
        raise AssertionError(
            "docs/architecture.md must be updated when events or callbacks change"
        )
