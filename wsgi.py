from __future__ import annotations

from yosai_intel_dashboard.src.core.env_validation import validate_required_env
from yosai_intel_dashboard.src.core.app_factory import create_app as _create_app


def create_app():
    validate_required_env()
    app = _create_app()
    return app.server


if __name__ == "__main__":
    import os
    import sys

    dev_mode = os.environ.get("YOSAI_DEV") == "1" or "--dev" in sys.argv
    if dev_mode:
        validate_required_env()
        app = _create_app()
        app.run()
    else:
        print(
            "Refusing to start the development server without --dev or YOSAI_DEV=1. "
            "Use 'gunicorn wsgi:create_app' or an equivalent WSGI server in production.",
        )
