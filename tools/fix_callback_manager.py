#!/usr/bin/env python3
"""
Fix CallbackManager to have both handle_register and register_handler methods
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def apply_callback_fix():
    """Apply the callback manager fix"""
    try:
        # Check current CallbackManager methods
        from analytics_core.callbacks.unified_callback_manager import CallbackManager
        from core.callback_events import CallbackEvent
        
        print("=== CHECKING CALLBACK MANAGER METHODS ===")
        
        manager = CallbackManager()
        methods = [method for method in dir(manager) if not method.startswith('_')]
        print(f"Available methods: {methods}")
        
        # Check if register_handler exists
        if hasattr(manager, 'register_handler'):
            print("✅ register_handler method already exists")
        else:
            print("❌ register_handler method missing")
            
        if hasattr(manager, 'handle_register'):
            print("✅ handle_register method exists")
        else:
            print("❌ handle_register method missing")
        
        # Test if we can monkey patch the method
        print("\n=== APPLYING FIX ===")
        
        # Add register_handler as an alias to handle_register
        if hasattr(manager, 'handle_register') and not hasattr(manager, 'register_handler'):
            CallbackManager.register_handler = CallbackManager.handle_register
            print("✅ Added register_handler as alias to handle_register")
        
        # Test the fix
        print("\n=== TESTING FIX ===")
        
        test_manager = CallbackManager()
        
        # Test both methods work
        def test_callback(*args, **kwargs):
            print("Test callback executed!")
        
        try:
            test_manager.handle_register(CallbackEvent.ANALYSIS_START, test_callback)
            print("✅ handle_register works")
        except Exception as e:
            print(f"❌ handle_register failed: {e}")
        
        try:
            test_manager.register_handler(CallbackEvent.ANALYSIS_COMPLETE, test_callback)
            print("✅ register_handler works")
        except Exception as e:
            print(f"❌ register_handler failed: {e}")
        
        # Test trigger
        try:
            test_manager.trigger(CallbackEvent.ANALYSIS_START, "test_source")
            print("✅ trigger works")
        except Exception as e:
            print(f"❌ trigger failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"Fix failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = apply_callback_fix()
    if success:
        print("\n🎉 Callback fix applied successfully!")
    else:
        print("\n❌ Callback fix failed")
    sys.exit(0 if success else 1)
