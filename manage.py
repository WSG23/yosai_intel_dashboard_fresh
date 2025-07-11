#!/usr/bin/env python3
"""Command line management for the Yōsai Intel Dashboard."""

import os
import sys
import click

from core.app_factory import create_app


@click.group()
def cli() -> None:
    """Management commands for the dashboard."""
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host address to bind")
@click.option("--port", default=8050, type=int, help="Port to listen on")
@click.option("--dev", is_flag=True, help="Run with the development server")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def runserver(host: str, port: int, dev: bool, debug: bool) -> None:
    """Run the dashboard server."""
    app = create_app()

    # When not explicitly using --dev, require YOSAI_DEV=1 to start the builtin server
    if dev or os.environ.get("YOSAI_DEV") == "1":
        app.run_server(host=host, port=str(port), debug=debug)
    else:
        click.echo(
            "Refusing to start the development server without --dev or YOSAI_DEV=1. "
            "Use 'gunicorn wsgi:server' or an equivalent WSGI server in production."
        )
        sys.exit(1)


if __name__ == "__main__":
    cli()
