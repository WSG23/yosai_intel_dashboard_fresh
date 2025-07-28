import start_api
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

if __name__ == "__main__":
    validate_env(REQUIRED_ENV_VARS)
    start_api.main()
