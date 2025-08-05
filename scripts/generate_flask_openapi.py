import json
import sys
from pathlib import Path

sys.path.insert(0, Path(__file__).resolve().parent.parent.as_posix())
from yosai_intel_dashboard.src.adapters.api.spec import create_spec


def main() -> None:
    spec = create_spec()
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    with open(docs_dir / "flask_openapi.json", "w", encoding="utf-8") as fh:
        json.dump(spec.to_dict(), fh, indent=2)


if __name__ == "__main__":
    main()
