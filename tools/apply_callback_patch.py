#!/usr/bin/env python3
"""
Permanent callback manager patch - adds register_handler alias
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Apply the fix globally when this module is imported
try:
    from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks as CallbackManager

    # Add register_handler as an alias to handle_register if it doesn't exist
    if hasattr(CallbackManager, "handle_register") and not hasattr(
        CallbackManager, "register_handler"
    ):
        CallbackManager.register_handler = CallbackManager.handle_register
        print("✅ CallbackManager patch applied: register_handler method added")

except ImportError:
    print("❌ Could not import CallbackManager for patching")


def ensure_callback_compatibility():
    """Ensure callback manager has both method names"""
    from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks as CallbackManager

    if not hasattr(CallbackManager, "register_handler"):
        CallbackManager.register_handler = CallbackManager.handle_register

    return True


if __name__ == "__main__":
    ensure_callback_compatibility()
    print("Callback compatibility ensured")
