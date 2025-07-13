#!/usr/bin/env python3
"""Fixed Main Application - No import issues"""
import logging
import os
import subprocess
import sys
from typing import Any, cast

from flask import Flask, request

try:
    from dotenv import load_dotenv
except ImportError:
    logging.error("Required package 'python-dotenv' is missing.")
    logging.error(
        "Run `pip install -r requirements.txt && pip install -r requirements-dev.txt` or `./scripts/setup.sh` to install dependencies."
    )
    sys.exit(1)

from core.exceptions import ConfigurationError
from utils import debug_dash_asset_serving
from core.unicode import unicode_safe_callback

import traceback
from pathlib import Path

from config import ConfigLoader

# This import is handled inside the main() function now

# Add Unicode handling
import locale
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        pass  # Fall back to default locale

logger = logging.getLogger(__name__)

# Environment / location check
def ensure_venv() -> None:
    """Ensure we're running from the project root and venv is active."""
    expected_files = ["requirements.txt", "app.py", "pages", "components"]
    current_files = os.listdir(".")

    if not all(f in current_files for f in expected_files):
        print("\u274c Wrong directory! Navigate to project root.")
        sys.exit(1)

    if not os.environ.get('VIRTUAL_ENV'):
        print("\u26a0\ufe0f Virtual environment not activated!")
        print("Run: source venv/bin/activate")

# Consolidated learning service utilities
from services.consolidated_learning_service import get_learning_service


def check_learning_status():
    """Check current learning status"""
    service = get_learning_service()
    stats = service.get_learning_statistics()

    logger.info("🧠 LEARNING STATUS:")
    logger.info(f"   Total learned files: {stats['total_mappings']}")
    logger.info(f"   Total devices learned: {stats['total_devices']}")
    logger.info(f"   Latest save: {stats.get('latest_save', 'None')}")

    logger.info("\n📁 LEARNED FILES:")
    for file_info in stats["files"]:
        logger.info(
            f"   • {file_info['filename']} - {file_info['device_count']} devices"
        )
        logger.info(f"     Fingerprint: {file_info['fingerprint']}")
        logger.info(f"     Saved: {file_info['saved_at']}")

    # Check if storage file exists
    import os

    storage_exists = os.path.exists("data/learned_mappings.json")
    logger.info(f"\n💾 Storage file exists: {storage_exists}")

    if storage_exists:
        file_size = os.path.getsize("data/learned_mappings.json")
        logger.info(f"   File size: {file_size} bytes")


def verify_dependencies() -> None:
    from utils.dependency_checker import verify_requirements

    verify_requirements("requirements.txt")


def print_startup_info(app_config):
    """Print application startup information"""
    logger.info("\n" + "=" * 60)
    logger.info("🏯 YŌSAI INTEL DASHBOARD")
    logger.info("=" * 60)
    logger.info(f"🌐 URL: http://{app_config.host}:{app_config.port}")
    logger.info(f"🔧 Debug Mode: {app_config.debug}")
    logger.info(f"🌍 Environment: {app_config.environment}")
    logger.info(f"📊 Analytics: http://{app_config.host}:{app_config.port}/analytics")
    logger.info(f"📁 Upload: http://{app_config.host}:{app_config.port}/upload")
    logger.info("=" * 60)

    if app_config.debug:
        logger.info("⚠️  Running in DEBUG mode - do not use in production!")

    logger.info("\n🚀 Dashboard starting...")


def ensure_https_certificates():
    """Auto-generate HTTPS certificates using mkcert if they don't exist"""
    cert_file = "localhost+1.pem"
    key_file = "localhost+1-key.pem"

    if os.path.exists(cert_file) and os.path.exists(key_file):
        logger.info("✅ HTTPS certificates found")
        return (cert_file, key_file)

    logger.info("📜 Generating HTTPS certificates...")

    try:
        subprocess.run(["mkcert", "-version"], capture_output=True, check=True)
        subprocess.run(["mkcert", "-install"], capture_output=True, check=True)
        logger.info("✅ Local CA installed")
        subprocess.run(
            ["mkcert", "localhost", "127.0.0.1"], capture_output=True, check=True
        )
        logger.info("✅ HTTPS certificates generated")
        return (cert_file, key_file)
    except subprocess.CalledProcessError:
        logger.error("❌ Failed to generate certificates with mkcert")
        return None
    except FileNotFoundError:
        logger.error("❌ mkcert not found - install with: brew install mkcert")
        logger.info("💡 Falling back to HTTP mode")
        return None


def _consolidate_callbacks(app):
    """Consolidate all callbacks with Unicode safety"""
    try:
        # Import callback modules with error handling
        callback_modules = [
            ('pages.deep_analytics_complex', 'register_callbacks'),
            ('pages.file_upload', 'register_callbacks'),
            ('pages.export', 'register_callbacks'),
            ('pages.settings', 'register_callbacks'),
        ]

        for module_name, func_name in callback_modules:
            try:
                module = __import__(module_name, fromlist=[func_name])
                if hasattr(module, func_name):
                    register_func = getattr(module, func_name)
                    # Apply Unicode safety wrapper
                    _apply_unicode_safety(app, register_func)
                    register_func(app)
                    logger.debug(f"✅ Registered callbacks from {module_name}")
            except ImportError:
                logger.debug(f"Module {module_name} not found, skipping")
            except Exception as e:
                logger.warning(f"Failed to register callbacks from {module_name}: {e}")

        logger.info("✅ All callbacks consolidated")

    except Exception as e:
        logger.error(f"❌ Callback consolidation failed: {e}")
        raise


def _apply_unicode_safety(app, register_func):
    """Apply Unicode safety to callback registration"""
    def safe_unicode_string(text):
        """Handle Unicode surrogate characters safely"""
        if not isinstance(text, str):
            return text
        try:
            return text.encode('utf-8', errors='ignore').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return text.encode('ascii', errors='ignore').decode('ascii')

    # Store original callback method
    original_callback = app.callback

    def handle_unicode_safe(*args, **kwargs):
        """Wrapper that adds Unicode safety to callbacks"""
        def decorator(func):
            import functools

            @functools.wraps(func)
            def wrapper(*cb_args, **cb_kwargs):
                try:
                    # Process string arguments safely
                    safe_args = []
                    for arg in cb_args:
                        if isinstance(arg, str):
                            safe_args.append(safe_unicode_string(arg))
                        elif isinstance(arg, (list, tuple)):
                            safe_args.append([safe_unicode_string(item) if isinstance(item, str) else item for item in arg])
                        else:
                            safe_args.append(arg)

                    # Process keyword arguments safely
                    safe_kwargs = {}
                    for key, value in cb_kwargs.items():
                        if isinstance(value, str):
                            safe_kwargs[key] = safe_unicode_string(value)
                        else:
                            safe_kwargs[key] = value

                    result = func(*safe_args, **safe_kwargs)

                    # Process result safely
                    if isinstance(result, str):
                        return safe_unicode_string(result)
                    elif isinstance(result, (list, tuple)):
                        return [safe_unicode_string(item) if isinstance(item, str) else item for item in result]

                    return result

                except Exception as e:
                    logger.error(f"Callback error: {e}")
                    # Return safe error response
                    return f"Error: {safe_unicode_string(str(e))}"

            return original_callback(*args, **kwargs)(wrapper)

        return decorator

    # Temporarily replace callback method
    app.callback = unicode_safe_callback

def main():
    """Main application entry point"""
    try:
        load_dotenv()

        # Set Unicode handling early
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

        from config.dev_mode import setup_dev_mode
        setup_dev_mode()

        # Import configuration
        try:
            loader = ConfigLoader()
            raw_cfg = loader.load()
            logger.debug("Loaded raw config with keys: %s", list(raw_cfg.keys()))

            from config import get_config
            config = get_config()
            app_config = config.get_app_config()
            logger.info("✅ Configuration loaded successfully")
            verify_dependencies()
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            logger.info(f"\n❌ Configuration Error: {e}")
            logger.info("💡 Make sure config/config.py exists and is properly formatted")
            sys.exit(1)

        # Print startup information
        print_startup_info(app_config)

        # Debug current working directory and asset existence
        cwd = os.getcwd()
        icon_path = os.path.normcase(
            os.path.join(cwd, "assets", "navbar_icons", "analytics.png")
        )
        logger.info("Current working directory: %s", cwd)
        logger.info("Analytics icon exists (%s): %s", icon_path, os.path.exists(icon_path))

        # Auto-generate HTTPS certificates
        ssl_context = ensure_https_certificates()

        # Validate secrets
        try:
            from core.secrets_manager import SecretsManager
            from security.secrets_validator import SecretsValidator

            secrets_manager = SecretsManager()
            validator = SecretsValidator(secrets_manager)

            if app_config.environment == 'production':
                secret_key: str = secrets_manager.get('SECRET_KEY', 'dev-key') or 'dev-key'
                result = validator.validate_secret(
                    secret_key,
                    environment='production'
                )
                if result.get('errors'):
                    raise ConfigurationError("Production secrets validation failed")

            logger.info("✅ Secrets validated successfully")
        except Exception as e:
            logger.error(f"❌ Secret validation failed: {e}")
            sys.exit(1)

        # Import and create the Dash application
        try:
            from core.app_factory import create_app
            project_root = Path(__file__).resolve().parent
            assets_dir = os.path.normcase(os.path.abspath(project_root / "assets"))
            app = create_app(mode='full', assets_folder=assets_dir)

            # Consolidate callbacks with Unicode safety
            # _register_callbacks(app, config, container=None)  # Already called during app creation

            # This avoids triggering a request before the hooks are in place
            if not debug_dash_asset_serving(app):
                logger.warning("Dash asset serving validation failed")
            logger.info("✅ Application created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create application: {e}")
            logger.info(f"\n❌ Application Creation Error: {e}")
            logger.info("💡 Make sure core/app_factory.py exists and dependencies are installed")
            sys.exit(1)

        # Run the application
        try:
            if ssl_context:
                logger.info("🔒 Starting with HTTPS")
                app.run_server(
                    host=app_config.host,
                    port=str(app_config.port),
                    debug=app_config.debug,
                    ssl_context=ssl_context,
                )
            else:
                logger.info("🌐 Starting with HTTP")
                app.run_server(
                    host=app_config.host,
                    port=str(app_config.port),
                    debug=app_config.debug,
                )

        except KeyboardInterrupt:
            logger.info("\n👋 Application stopped by user")
        except Exception as e:
            logger.error(f"❌ Application runtime error: {e}")
            logger.info(f"\n❌ Runtime Error: {e}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.info(f"\n❌ Unexpected Error: {e}")
        logger.info("💡 Check logs for more details")
        sys.exit(1)


if __name__ == "__main__":
    ensure_venv()
    main()
    check_learning_status()
