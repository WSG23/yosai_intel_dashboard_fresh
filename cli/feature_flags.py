"""CLI to manage feature flags via the API."""

from __future__ import annotations

import argparse
import json
import logging
from urllib.parse import urlparse
from typing import Any, Sequence

import requests

from yosai_intel_dashboard.src.exceptions import (
    ExternalServiceError,
    InvalidResponseError,
)
from yosai_intel_dashboard.src.logging_config import configure_logging

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 5


def _headers(token: str | None, roles: str | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if roles:
        headers["X-Roles"] = roles
    return headers


def _validate_url(url: str) -> str:
    """Validate that ``url`` has an http or https scheme and netloc."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    return url


def list_flags(api_url: str, token: str | None, roles: str | None) -> list[dict[str, Any]]:
    try:
        resp = requests.get(
            api_url, headers=_headers(token, roles), timeout=DEFAULT_TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:  # pragma: no cover - network error
        logger.error("Failed to list feature flags: %s", exc)
        raise ExternalServiceError("Failed to list feature flags") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - malformed response
        logger.error("Invalid JSON in feature flag response: %s", exc)
        raise InvalidResponseError("Invalid feature flag response") from exc

    logger.info("Retrieved %d feature flags", len(data))
    return data


def get_flag(
    api_url: str, name: str, token: str | None, roles: str | None
) -> dict[str, Any]:
    try:
        resp = requests.get(
            f"{api_url}/{name}",
            headers=_headers(token, roles),
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:  # pragma: no cover - network error
        logger.error("Failed to get feature flag %s: %s", name, exc)
        raise ExternalServiceError(
            f"Failed to get feature flag '{name}'"
        ) from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - malformed response
        logger.error("Invalid JSON in get flag response: %s", exc)
        raise InvalidResponseError("Invalid feature flag response") from exc

    logger.info("Retrieved feature flag '%s'", name)
    return data


def create_flag(
    api_url: str, name: str, enabled: bool, token: str | None, roles: str | None
) -> dict[str, Any]:
    payload = {"name": name, "enabled": enabled}
    try:
        resp = requests.post(
            api_url,
            json=payload,
            headers=_headers(token, roles),
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:  # pragma: no cover - network error
        logger.error("Failed to create feature flag %s: %s", name, exc)
        raise ExternalServiceError(
            f"Failed to create feature flag '{name}'"
        ) from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - malformed response
        logger.error("Invalid JSON in create flag response: %s", exc)
        raise InvalidResponseError("Invalid feature flag response") from exc

    logger.info("Created feature flag '%s'", name)
    return data


def update_flag(
    api_url: str, name: str, enabled: bool, token: str | None, roles: str | None
) -> dict[str, Any]:
    payload = {"enabled": enabled}
    try:
        resp = requests.put(
            f"{api_url}/{name}",
            json=payload,
            headers=_headers(token, roles),
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:  # pragma: no cover - network error
        logger.error("Failed to update feature flag %s: %s", name, exc)
        raise ExternalServiceError(
            f"Failed to update feature flag '{name}'"
        ) from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - malformed response
        logger.error("Invalid JSON in update flag response: %s", exc)
        raise InvalidResponseError("Invalid feature flag response") from exc

    logger.info("Updated feature flag '%s'", name)
    return data


def delete_flag(api_url: str, name: str, token: str | None, roles: str | None) -> None:
    try:
        resp = requests.delete(
            f"{api_url}/{name}",
            headers=_headers(token, roles),
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network error
        logger.error("Failed to delete feature flag %s: %s", name, exc)
        raise ExternalServiceError(
            f"Failed to delete feature flag '{name}'"
        ) from exc

    logger.info("Deleted feature flag '%s'", name)


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
    sp.set_defaults(
        func=lambda args: list_flags(
            _validate_url(args.api_url), args.token, args.roles
        )
    )

    sp = sub.add_parser("get", help="Get a flag")
    sp.add_argument("name")
    sp.set_defaults(
        func=lambda args: get_flag(
            _validate_url(args.api_url), args.name, args.token, args.roles
        )
    )

    sp = sub.add_parser("create", help="Create a flag")
    sp.add_argument("name")
    sp.add_argument("--enabled", action="store_true", help="Enable the flag")
    sp.set_defaults(
        func=lambda args: create_flag(
            _validate_url(args.api_url),
            args.name,
            args.enabled,
            args.token,
            args.roles,
        )
    )

    sp = sub.add_parser("update", help="Update a flag")
    sp.add_argument("name")
    sp.add_argument("--enabled", action="store_true", help="Enable the flag")
    sp.set_defaults(
        func=lambda args: update_flag(
            _validate_url(args.api_url),
            args.name,
            args.enabled,
            args.token,
            args.roles,
        )
    )

    sp = sub.add_parser("delete", help="Delete a flag")
    sp.add_argument("name")
    sp.set_defaults(
        func=lambda args: delete_flag(
            _validate_url(args.api_url), args.name, args.token, args.roles
        )
    )

    args = parser.parse_args(argv)
    configure_logging()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    result = args.func(args)
    if result is not None:
        logger.debug(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
