from core.app_factory import create_app
from core.env_validation import validate_env

REQUIRED_ENV_VARS = [
    "SECRET_KEY",
    "DB_PASSWORD",
    "AUTH0_CLIENT_ID",
    "AUTH0_CLIENT_SECRET",
    "AUTH0_DOMAIN",
    "AUTH0_AUDIENCE",
    "JWT_SECRET",
]

validate_env(REQUIRED_ENV_VARS)

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
