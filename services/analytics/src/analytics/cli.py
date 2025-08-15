"""Simple command line interface for analytics tasks."""

from __future__ import annotations

import argparse

from yosai_intel_dashboard.src.services.analytics_service import create_analytics_service


def main(argv: list[str] | None = None) -> None:
    """Run basic analytics commands.

    The current CLI supports a single ``--preload-models`` flag which
    preloads any active models and then exits.  It acts primarily as a
    lightweight example demonstrating how the analytics package can expose
    a CLI entrypoint separate from the FastAPI service.
    """

    parser = argparse.ArgumentParser(description="Analytics CLI")
    parser.add_argument(
        "--preload-models",
        action="store_true",
        help="Preload active models into memory and exit",
    )
    args = parser.parse_args(argv)

    service = create_analytics_service()
    if args.preload_models:
        service.preload_active_models()


if __name__ == "__main__":  # pragma: no cover
    main()
