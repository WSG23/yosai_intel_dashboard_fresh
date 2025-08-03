from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click

ROOT = Path(__file__).resolve().parent.parent
COMPOSE_DEV_FILES = [
    "docker-compose.yml",
    "docker-compose.kafka.yml",
    "docker-compose.dev.yml",
]
COMPOSE_PROD_FILE = "docker-compose.prod.yml"
COMPOSE_ALL_FILE = "docker-compose.unified.yml"


def run(cmd):
    result = subprocess.run(cmd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def compose_args(files):
    args = []
    for f in files:
        args.extend(["-f", str(ROOT / f)])
    return args


@click.group()
def cli():
    """Unified Operations Platform helper."""


@cli.command("validate-config")
def validate_config():
    """Validate environment and configuration."""
    from scripts.production_setup import validate_environment

    validate_environment()
    click.echo("Configuration validated")


@cli.command()
def build():
    """Build Docker images."""
    run(["docker", "compose", *compose_args(COMPOSE_DEV_FILES), "build"])


@cli.command()
def deploy():
    """Start services using Docker Compose."""
    run(["docker", "compose", *compose_args(COMPOSE_DEV_FILES), "up", "-d"])


@cli.command("build-all")
def build_all():
    """Build all service images for the unified stack."""
    run(["docker", "compose", "-f", str(ROOT / COMPOSE_ALL_FILE), "build"])


@cli.command("deploy-all")
def deploy_all():
    """Start the entire unified stack."""
    run(["docker", "compose", "-f", str(ROOT / COMPOSE_ALL_FILE), "up", "-d"])


@cli.command("test-all")
def test_all():
    """Run full test suite."""
    run(["pytest"])


@cli.command()
@click.argument("service")
def logs(service):
    """Tail logs for a specific service."""
    run(
        [
            "docker",
            "compose",
            "-f",
            str(ROOT / COMPOSE_ALL_FILE),
            "logs",
            "-f",
            service,
        ]
    )


@cli.command()
def test():
    """Run the test suite."""
    run(["pytest"])


@cli.command("frontend-build")
def frontend_build():
    """Build frontend assets using npm."""
    run(["npm", "run", "build"])


@cli.command("frontend-test")
def frontend_test():
    """Run frontend unit tests."""
    run(["npm", "test", "--", "--watchAll=false"])


@cli.command()
def format():
    """Format code with black and isort."""
    run(["isort", "."])
    run(["black", "."])


@cli.command()
def lint():
    """Run flake8 lint checks."""
    run(["flake8", "."])
    run([sys.executable, "tools/check_execute_query.py"])


@cli.command()
def clean():
    """Remove temporary files and stop containers."""
    run(["docker", "compose", *compose_args(COMPOSE_DEV_FILES), "down", "-v"])
    for path in ROOT.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":  # pragma: no cover - manual tool
    cli()
