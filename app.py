#!/usr/bin/env python3
"""Fixed Main Application - No import issues"""
import sys
import subprocess

def check_and_install_critical_deps():
    critical = ['psutil', 'chardet', 'pandas', 'dash', 'flask']
    missing = []
    for pkg in critical:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Installing missing: {missing}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)

check_and_install_critical_deps()

import logging
import os
from flask import request

try:
    from dotenv import load_dotenv
except ImportError:
    logging.error("Required package 'python-dotenv' is missing.")
    logging.error(
        "Run `pip install -r requirements.txt` or `./scripts/setup.sh` to install dependencies."
    )
    sys.exit(1)

from core.exceptions import ConfigurationError
from utils import debug_dash_asset_serving

logger = logging.getLogger(__name__)

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


def main():
    """Main application entry point"""
    try:
        load_dotenv()
        from config.dev_mode import setup_dev_mode

        setup_dev_mode()
        # Import configuration
        try:
            from config.config import get_config

            config = get_config()
            app_config = config.get_app_config()
            logger.info("✅ Configuration loaded successfully")
            verify_dependencies()
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            logger.info(f"\n❌ Configuration Error: {e}")
            logger.info(
                "💡 Make sure config/config.py exists and is properly formatted"
            )
            sys.exit(1)

        # Print startup information
        print_startup_info(app_config)

        # Auto-generate HTTPS certificates
        ssl_context = ensure_https_certificates()

        try:
            from core.secrets_validator import validate_all_secrets

            validated = validate_all_secrets()
            for k, v in validated.items():
                os.environ.setdefault(k, v)
            logger.info("✅ Secrets validated successfully")
        except ConfigurationError as e:
            logger.error(f"❌ Secret validation failed: {e}")
            sys.exit(1)

        # Import and create the Dash application
        try:
            from core.app_factory import create_app
            from security.validation_middleware import ValidationMiddleware
            from core.callback_manager import CallbackManager
            from core.callback_events import CallbackEvent

            app = create_app()
            middleware = ValidationMiddleware()
            manager = CallbackManager()
            middleware.register_callbacks(manager)

            server = app.server

            @server.before_request
            def _before_request():
                logger.debug("Incoming request scheme: %s", request.scheme)
                for result in manager.trigger(CallbackEvent.BEFORE_REQUEST):
                    if result is not None:
                        return result

            @server.after_request
            def _after_request(response):
                current = response
                for cb in manager.get_callbacks(CallbackEvent.AFTER_REQUEST):
                    try:
                        r = cb[1](current)
                        if r is not None:
                            current = r
                    except Exception as exc:  # pragma: no cover - log and continue
                        logging.getLogger(__name__).exception(
                            "after_request callback failed: %s", exc
                        )
                manager.trigger(CallbackEvent.AFTER_REQUEST, current)
                return current

            app._callback_manager = manager  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
            # Validate that Dash can serve static assets after request hooks
            # have been registered. This avoids triggering a request before the
            # hooks are in place, which previously caused Flask to raise a
            # setup error.
            if not debug_dash_asset_serving(app):
                logger.warning("Dash asset serving validation failed")
            logger.info("✅ Application created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create application: {e}")
            logger.info(f"\n❌ Application Creation Error: {e}")
            logger.info(
                "💡 Make sure core/app_factory.py exists and dependencies are installed"
            )
            sys.exit(1)

        # Run the application
        try:
            if ssl_context:
                logger.info("🔒 Starting with HTTPS")
                app.run(
                    host=app_config.host,
                    port=app_config.port,
                    debug=app_config.debug,
                    ssl_context=ssl_context,
                )
            else:
                logger.info("🌐 Starting with HTTP")
                app.run(
                    host=app_config.host,
                    port=app_config.port,
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
    main()
    check_learning_status()
