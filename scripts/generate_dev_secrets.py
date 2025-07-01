#!/usr/bin/env python3
"""Generate strong random secret values for development.

Outputs SECRET_KEY and DB_PASSWORD lines using `secrets.token_urlsafe`.
"""
import secrets


def main() -> None:
    print(f"SECRET_KEY={secrets.token_urlsafe(32)}")
    print(f"DB_PASSWORD={secrets.token_urlsafe(32)}")


if __name__ == "__main__":
    main()
