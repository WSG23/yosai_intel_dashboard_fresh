#!/usr/bin/env python3
"""
Asset generator utility to create missing navbar icons.
Run this script to generate the missing PNG files.
"""

import logging
from pathlib import Path
from typing import Dict, List

try:
    from PIL import Image, ImageDraw, ImageFont

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from yosai_intel_dashboard.src.core.unicode import safe_encode_text

logger = logging.getLogger(__name__)

# Asset directory
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
NAVBAR_ICON_DIR = ASSETS_DIR / "navbar_icons"

# Icon definitions
ICON_DEFINITIONS = {
    "analytics": {"color": "#007bff", "symbol": "📊"},
    "upload": {"color": "#28a745", "symbol": "📁"},
    "settings": {"color": "#6c757d", "symbol": "⚙️"},
    "graphs": {"color": "#17a2b8", "symbol": "📈"},
    "export": {"color": "#fd7e14", "symbol": "📤"},
}


def create_simple_svg_icon(name: str, color: str, symbol: str) -> str:
    """
    Create simple SVG icon content.

    Args:
        name: Icon name
        color: Hex color code
        symbol: Unicode symbol to use

    Returns:
        SVG content as string
    """
    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <rect width="16" height="16" rx="2" fill="{color}" opacity="0.1"/>
    <text x="8" y="12" text-anchor="middle" font-family="Arial, sans-serif" 
          font-size="10" fill="{color}">{symbol}</text>
</svg>"""
    return svg_content


def create_png_from_svg(svg_content: str, output_path: Path) -> bool:
    """
    Convert SVG to PNG using PIL if available.

    Args:
        svg_content: SVG content string
        output_path: Output PNG file path

    Returns:
        True if successful, False otherwise
    """
    if not PIL_AVAILABLE:
        return False

    try:
        # For simplicity, create a basic colored rectangle with PIL
        img = Image.new("RGBA", (16, 16), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)

        # Extract color from SVG (simple parsing)
        if 'fill="#007bff"' in svg_content:
            color = (0, 123, 255, 255)
        elif 'fill="#28a745"' in svg_content:
            color = (40, 167, 69, 255)
        elif 'fill="#6c757d"' in svg_content:
            color = (108, 117, 125, 255)
        elif 'fill="#17a2b8"' in svg_content:
            color = (23, 162, 184, 255)
        else:
            color = (253, 126, 20, 255)

        # Draw simple icon shape
        draw.rectangle([1, 1, 15, 15], fill=color, outline=None)
        draw.rectangle([3, 3, 13, 13], fill=(255, 255, 255, 200))

        # Save as PNG
        img.save(output_path, "PNG")
        return True

    except Exception as e:
        logger.error(f"Failed to create PNG from SVG: {e}")
        return False


def create_placeholder_png(
    output_path: Path, color: tuple = (108, 117, 125, 255)
) -> bool:
    """
    Create placeholder PNG file when PIL is not available.

    Args:
        output_path: Output PNG file path
        color: RGBA color tuple

    Returns:
        True if successful, False otherwise
    """
    if not PIL_AVAILABLE:
        # Create empty file as placeholder
        try:
            output_path.touch()
            return True
        except Exception:
            return False

    try:
        img = Image.new("RGBA", (16, 16), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 15, 15], fill=color)
        img.save(output_path, "PNG")
        return True
    except Exception as e:
        logger.error(f"Failed to create placeholder PNG: {e}")
        return False


def ensure_navbar_icon_directory() -> bool:
    """
    Ensure navbar icon directory exists.

    Returns:
        True if directory exists or was created successfully
    """
    try:
        NAVBAR_ICON_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create navbar icon directory: {e}")
        return False


def create_missing_icons() -> Dict[str, bool]:
    """
    Create missing navbar icons.

    Returns:
        Dictionary mapping icon names to creation success status
    """
    results = {}

    if not ensure_navbar_icon_directory():
        logger.error("Cannot create navbar icon directory")
        return results

    for icon_name, icon_config in ICON_DEFINITIONS.items():
        icon_path = NAVBAR_ICON_DIR / f"{icon_name}.png"

        if icon_path.exists():
            logger.info(f"Icon already exists: {icon_name}.png")
            results[icon_name] = True
            continue

        try:
            # Create SVG content
            svg_content = create_simple_svg_icon(
                icon_name, icon_config["color"], icon_config["symbol"]
            )

            # Try to create PNG from SVG
            success = create_png_from_svg(svg_content, icon_path)

            if not success:
                # Fallback to simple placeholder
                success = create_placeholder_png(icon_path)

            results[icon_name] = success

            if success:
                logger.info(f"Created icon: {icon_name}.png")
            else:
                logger.error(f"Failed to create icon: {icon_name}.png")

        except Exception as e:
            logger.error(f"Error creating icon {icon_name}: {e}")
            results[icon_name] = False

    return results


def check_existing_icons() -> List[str]:
    """
    Check which navbar icons already exist.

    Returns:
        List of existing icon names (without .png extension)
    """
    existing = []

    if not NAVBAR_ICON_DIR.exists():
        return existing

    for icon_name in ICON_DEFINITIONS.keys():
        icon_path = NAVBAR_ICON_DIR / f"{icon_name}.png"
        if icon_path.exists():
            existing.append(icon_name)

    return existing


def main():
    """
    Main function to create missing navbar assets.
    """
    logger.info("🎨 Creating Navbar Assets")
    logger.info("=" * 50)

    # Check existing icons
    existing = check_existing_icons()
    logger.info(f"📁 Existing icons: {', '.join(existing) if existing else 'None'}")

    # Create missing icons
    results = create_missing_icons()

    # Report results
    successful = [name for name, success in results.items() if success]
    failed = [name for name, success in results.items() if not success]

    logger.info(
        f"\n✅ Successfully created: {', '.join(successful) if successful else 'None'}"
    )
    logger.info(f"❌ Failed to create: {', '.join(failed) if failed else 'None'}")

    if not PIL_AVAILABLE:
        logger.warning("\n⚠️  PIL/Pillow not available - created placeholder files")
        logger.warning(
            "   Install Pillow for better icon generation: pip install Pillow"
        )

    total_created = len(successful)
    total_icons = len(ICON_DEFINITIONS)

    logger.info(f"\n📊 Summary: {total_created}/{total_icons} icons available")

    if total_created == total_icons:
        logger.info("🎉 All navbar icons created successfully!")
    elif total_created > 0:
        logger.info(
            "⚠️  Some icons created - navbar will use FontAwesome fallbacks for missing icons"
        )
    else:
        logger.info("❌ No icons created - navbar will use FontAwesome fallbacks")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
