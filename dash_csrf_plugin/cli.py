"""
Command-line interface for CSRF plugin
"""

import json
import sys
from typing import Any, Dict

import click

from yosai_intel_dashboard.src.infrastructure.config.constants import DEFAULT_APP_PORT

from .config import CSRFConfig, CSRFMode
from .plugin import DashCSRFPlugin
from .utils import CSRFUtils


@click.group()
@click.version_option()
def cli():
    """Dash CSRF Protection Plugin CLI"""
    pass


@cli.command()
@click.option("--config-file", "-c", help="Path to configuration file")
@click.option("--secret-key", "-s", help="Secret key to validate")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["development", "production", "testing", "enabled", "disabled"]),
    default="auto",
    help="CSRF mode to check",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def check_csrf(config_file, secret_key, mode, verbose):
    """Check CSRF configuration and security"""
    click.echo("🛡️  Dash CSRF Protection Plugin - Security Check")
    click.echo("=" * 50)

    try:
        # Load configuration
        if config_file:
            config = CSRFConfig.from_dict(json.load(open(config_file)))
        else:
            config = CSRFConfig()

        if secret_key:
            config.secret_key = secret_key

        # Validate configuration
        issues = CSRFUtils.validate_config_security(config.to_dict())

        # Display results
        click.echo(f"Configuration Mode: {mode}")
        click.echo(f"CSRF Enabled: {config.enabled}")
        click.echo(f"Secret Key Set: {'Yes' if config.secret_key else 'No'}")
        click.echo(f"SSL Strict: {config.ssl_strict}")
        click.echo(f"Time Limit: {config.time_limit} seconds")
        click.echo()

        # Security issues
        if issues["errors"]:
            click.echo("❌ Critical Issues:")
            for error in issues["errors"]:
                click.echo(f"  • {error}", err=True)
            click.echo()

        if issues["warnings"]:
            click.echo("⚠️  Warnings:")
            for warning in issues["warnings"]:
                click.echo(f"  • {warning}")
            click.echo()

        if issues["recommendations"]:
            click.echo("💡 Recommendations:")
            for rec in issues["recommendations"]:
                click.echo(f"  • {rec}")
            click.echo()

        # Overall status
        if not issues["errors"]:
            click.echo("✅ CSRF configuration looks good!")
            sys.exit(0)
        else:
            click.echo("❌ CSRF configuration has issues that need attention")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error checking CSRF configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--length", "-l", default=32, help="Secret key length")
def generate_key(length):
    """Generate a secure secret key"""
    key = CSRFUtils.generate_secret_key(length)
    click.echo("🔑 Generated Secret Key:")
    click.echo(key)
    click.echo()
    click.echo(
        "💡 Store this key securely and set it as your SECRET_KEY environment variable:"
    )
    click.echo(f"export SECRET_KEY='{key}'")


@cli.command()
@click.argument("app_module")
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to")
@click.option("--port", "-p", default=DEFAULT_APP_PORT, help="Port to bind to")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def run(app_module, host, port, debug):
    """Run a Dash app with CSRF protection"""
    try:
        # Import the app module
        import importlib

        module = importlib.import_module(app_module)

        if hasattr(module, "app"):
            app = module.app
        elif hasattr(module, "application"):
            app = module.application
        else:
            click.echo("❌ Could not find 'app' or 'application' in module", err=True)
            sys.exit(1)

        # Check if CSRF plugin is configured
        if hasattr(app, "_plugins") and "csrf" in app._plugins:
            csrf_plugin = app._plugins["csrf"]
            click.echo(f"✅ CSRF Plugin detected (Mode: {csrf_plugin.mode.value})")
        else:
            click.echo("⚠️  No CSRF plugin detected in app")

        # Run the app
        click.echo(f"🚀 Starting Dash app on {host}:{port}")
        app.run(host=host, port=port, debug=debug)

    except ImportError as e:
        click.echo(f"❌ Could not import module '{app_module}': {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error running app: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("output_file")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["development", "production", "testing"]),
    default="development",
    help="Configuration mode",
)
@click.option("--secret-key", "-s", help="Secret key (generated if not provided)")
def init_config(output_file, mode, secret_key):
    """Initialize a CSRF configuration file"""
    try:
        # Generate secret key if not provided
        if not secret_key:
            secret_key = CSRFUtils.generate_secret_key()

        # Create configuration based on mode
        if mode == "development":
            config = CSRFConfig.for_development(secret_key=secret_key)
        elif mode == "production":
            config = CSRFConfig.for_production(secret_key)
        elif mode == "testing":
            config = CSRFConfig.for_testing(secret_key=secret_key)

        # Write configuration file
        config_dict = config.to_dict()
        config_dict["secret_key"] = secret_key  # Include actual secret key

        with open(output_file, "w") as f:
            json.dump(config_dict, f, indent=2)

        click.echo(f"✅ Configuration file created: {output_file}")
        click.echo(f"📋 Mode: {mode}")
        click.echo(f"🔐 Secret key included in file - keep it secure!")

    except Exception as e:
        click.echo(f"❌ Error creating configuration: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
