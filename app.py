#!/usr/bin/env python3
"""
Fixed Main Application - No import issues
"""
import logging
import os
import sys

# Configure logging first
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Initialize global device learning service
from services.device_learning_service import DeviceLearningService
from services.consolidated_learning_service import get_learning_service

learning_service = DeviceLearningService()


def check_learning_status():
    """Check current learning status"""
    service = get_learning_service()
    stats = service.get_learning_statistics()

    logger.info("🧠 LEARNING STATUS:")
    logger.info(f"   Total learned files: {stats['total_mappings']}")
    logger.info(f"   Total devices learned: {stats['total_devices']}")
    logger.info(f"   Latest save: {stats.get('latest_save', 'None')}")

    logger.info("\n📁 LEARNED FILES:")
    for file_info in stats['files']:
        logger.info(f"   • {file_info['filename']} - {file_info['device_count']} devices")
        logger.info(f"     Fingerprint: {file_info['fingerprint']}")
        logger.info(f"     Saved: {file_info['saved_at']}")

    # Check if storage file exists
    import os
    storage_exists = os.path.exists("data/learned_mappings.json")
    logger.info(f"\n💾 Storage file exists: {storage_exists}")

    if storage_exists:
        file_size = os.path.getsize("data/learned_mappings.json")
        logger.info(f"   File size: {file_size} bytes")


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


def main():
    """Main application entry point"""
    try:
        # Import configuration
        try:
            from config.config import get_config

            config = get_config()
            app_config = config.get_app_config()
            logger.info("✅ Configuration loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            logger.info(f"\n❌ Configuration Error: {e}")
            logger.info("💡 Make sure config/config.py exists and is properly formatted")
            sys.exit(1)

        # Print startup information
        print_startup_info(app_config)

        # Import and create the Dash application
        try:
            from core.app_factory import create_app

            app = create_app()
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
            app.run(
                debug=app_config.debug, host=app_config.host, port=app_config.port
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
