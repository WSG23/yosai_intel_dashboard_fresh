"""CLI to manage feature flags via the API."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

import requests


def _headers(token: str | None, roles: str | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if roles:
        headers["X-Roles"] = roles
    return headers


def list_flags(api_url: str, token: str | None, roles: str | None) -> None:
    resp = requests.get(api_url, headers=_headers(token, roles))
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))


def get_flag(api_url: str, name: str, token: str | None, roles: str | None) -> None:
    resp = requests.get(f"{api_url}/{name}", headers=_headers(token, roles))
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))


def create_flag(
    api_url: str, name: str, enabled: bool, token: str | None, roles: str | None
) -> None:
    payload = {"name": name, "enabled": enabled}
    resp = requests.post(api_url, json=payload, headers=_headers(token, roles))
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))


def update_flag(
    api_url: str, name: str, enabled: bool, token: str | None, roles: str | None
) -> None:
    payload = {"enabled": enabled}
    resp = requests.put(
        f"{api_url}/{name}", json=payload, headers=_headers(token, roles)
    )
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))


def delete_flag(api_url: str, name: str, token: str | None, roles: str | None) -> None:
    resp = requests.delete(f"{api_url}/{name}", headers=_headers(token, roles))
    resp.raise_for_status()
    print("deleted")


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Manage feature flags via API")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000/v1/feature-flags",
        help="Feature flag API base URL",
    )
    parser.add_argument("--token", help="Bearer token for authentication")
    parser.add_argument("--roles", help="Comma separated roles for RBAC")

    sub = parser.add_subparsers(dest="command")

    sp = sub.add_parser("list", help="List all feature flags")
    sp.set_defaults(func=lambda args: list_flags(args.api_url, args.token, args.roles))

    sp = sub.add_parser("get", help="Get a flag")
    sp.add_argument("name")
    sp.set_defaults(
        func=lambda args: get_flag(args.api_url, args.name, args.token, args.roles)
    )

    sp = sub.add_parser("create", help="Create a flag")
    sp.add_argument("name")
    sp.add_argument("--enabled", action="store_true", help="Enable the flag")
    sp.set_defaults(
        func=lambda args: create_flag(
            args.api_url, args.name, args.enabled, args.token, args.roles
        )
    )

    sp = sub.add_parser("update", help="Update a flag")
    sp.add_argument("name")
    sp.add_argument("--enabled", action="store_true", help="Enable the flag")
    sp.set_defaults(
        func=lambda args: update_flag(
            args.api_url, args.name, args.enabled, args.token, args.roles
        )
    )

    sp = sub.add_parser("delete", help="Delete a flag")
    sp.add_argument("name")
    sp.set_defaults(
        func=lambda args: delete_flag(args.api_url, args.name, args.token, args.roles)
    )

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
