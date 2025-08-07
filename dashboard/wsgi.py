from __future__ import annotations

from yosai_intel_dashboard.src.core.env_validation import validate_required_env
from yosai_intel_dashboard.src.core.app_factory import create_app

validate_required_env()

app = create_app()
server = app.server

if __name__ == "__main__":
    import os
    import sys

    dev_mode = os.environ.get("YOSAI_DEV") == "1" or "--dev" in sys.argv
    if dev_mode:
        app.run()
    else:
        print(
            "Refusing to start the development server without --dev or YOSAI_DEV=1. "
            "Use 'gunicorn wsgi:server' or an equivalent WSGI server in production."
        )
