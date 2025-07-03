#!/usr/bin/env python3
"""
Updated app.py with LazyString Fix Integration
This shows how to modify your existing app.py to fix the LazyString error
This script is kept as a legacy sample plugin for reference and is not used by the application.

"""

import os
import logging
from flask import Flask
from flask_login import login_required
from flask_babel import Babel

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import the application factory
from core.app_factory import create_app

# Import the LazyString fix implementation
from plugins.lazystring_fix_plugin import (
    initialize_lazystring_fix,
    LazyStringFixConfig,
)


def create_app_with_lazystring_fix():
    """Create the Yosai app with LazyString fix applied"""

    logger.info("Creating Yosai Intel Dashboard with LazyString fix...")

    # Create the app using your existing factory
    app = create_app()

    if app is None:
        logger.error("Failed to create application")
        return None

    # Apply the LazyString fix
    # This MUST be done after app creation but before running
    try:
        config = LazyStringFixConfig(
            enabled=True,
            auto_wrap_callbacks=True,  # Automatically wrap all callbacks
            deep_sanitize=True,  # Handle nested objects
            log_conversions=True,  # Log for debugging (set False in production)
            fallback_locale="en",  # Default locale for errors
        )

        plugin = initialize_lazystring_fix(app, config)
        logger.info("✅ LazyString fix applied successfully")

        # Log statistics
        stats = plugin.get_stats()
        logger.info(f"LazyString plugin initialized: {stats}")

    except Exception as e:
        logger.error(f"Failed to apply LazyString fix: {e}")
        # Continue anyway - app might still work for non-i18n parts

    return app


# Alternative: Minimal change to existing app.py
def patch_existing_app_minimal():
    """
    If you have an existing app.py and want minimal changes,
    just add these 3 lines after creating your app:
    """

    # Your existing code to create app
    app = create_app()

    # Add these 3 lines to fix LazyString:
    from plugins.lazystring_fix_plugin import (
        initialize_lazystring_fix,
        LazyStringFixConfig,
    )

    config = LazyStringFixConfig(auto_wrap_callbacks=True, deep_sanitize=True)
    initialize_lazystring_fix(app, config)

    return app


# Production-ready initialization
def create_production_app():
    """Production configuration with error handling"""

    try:
        # Create base app
        app = create_app()

        if app is None:
            raise RuntimeError("App creation failed")

        # Apply LazyString fix with production config
        lazystring_config = LazyStringFixConfig(
            enabled=True,
            auto_wrap_callbacks=True,
            deep_sanitize=True,
            log_conversions=False,  # Disable logging in production
            fallback_locale=os.getenv("DEFAULT_LOCALE", "en"),
        )

        plugin = initialize_lazystring_fix(app, lazystring_config)

        # Verify the fix is working
        test_result = _verify_lazystring_fix(app)
        if not test_result:
            logger.warning("LazyString fix verification failed, but continuing...")

        logger.info("Production app created with LazyString protection")
        return app

    except Exception as e:
        logger.error(f"Failed to create production app: {e}")
        raise


def _verify_lazystring_fix(app):
    """Verify that LazyString fix is working"""

    try:
        from flask_babel import lazy_gettext as _l
        import json

        # Test LazyString handling
        test_obj = {
            "message": _l("Test message"),
            "nested": {"items": [_l("Item 1"), _l("Item 2")]},
        }

        # This should not raise an error if fix is working
        from plugins.lazystring_fix_plugin import sanitize_lazystring

        sanitized = sanitize_lazystring(test_obj)
        json.dumps(sanitized)

        logger.info("✅ LazyString fix verified working")
        return True

    except Exception as e:
        logger.error(f"❌ LazyString fix verification failed: {e}")
        return False


# Main entry point
if __name__ == "__main__":
    # Use environment variable to select mode
    mode = os.getenv("APP_MODE", "development")

    if mode == "production":
        app = create_production_app()
    else:
        app = create_app_with_lazystring_fix()

    if app is not None:
        # Get server from Dash app
        server = app.server

        # Run based on environment
        if mode == "production":
            # Production: Let gunicorn or other WSGI server handle it
            logger.info("App created for production deployment")
        else:
            # Development: Run with Flask dev server
            debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
            port = int(os.getenv("PORT", "8050"))
            host = os.getenv("HOST", "127.0.0.1")

            logger.info(f"Starting development server on {host}:{port}")
            app.run(debug=debug, host=host, port=port, dev_tools_hot_reload=debug)
    else:
        logger.error("Failed to start application")
        exit(1)


# For gunicorn or other WSGI servers
server = create_production_app().server if __name__ != "__main__" else None
