#!/usr/bin/env python3
"""
Add missing register_callback method to TrulyUnifiedCallbacks class
"""
import re
from pathlib import Path

def add_register_callback_method():
    """Add the missing register_callback method to TrulyUnifiedCallbacks"""
    
    file_path = Path("core/truly_unified_callbacks.py")
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if register_callback method already exists
    if 'def register_callback(' in content:
        print("✅ register_callback method already exists!")
        return True
    
    # Find the location to insert the method (after handle_register method)
    # Look for the end of handle_register method
    pattern = r'(def handle_register\(.*?\n.*?return decorator\n)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ Could not find handle_register method to insert after")
        return False
    
    # The method to add
    register_callback_method = '''
    # ------------------------------------------------------------------
    def register_callback(
        self,
        outputs: Any,
        inputs: Iterable[Input] | Input | None = None,
        states: Iterable[State] | State | None = None,
        *,
        callback_id: str,
        component_name: str,
        allow_duplicate: bool = False,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Alias for handle_register method - register a Dash callback and track conflicts."""
        return self.handle_register(
            outputs=outputs,
            inputs=inputs,
            states=states,
            callback_id=callback_id,
            component_name=component_name,
            allow_duplicate=allow_duplicate,
            **kwargs
        )
'''
    
    # Insert the method after handle_register
    insert_position = match.end()
    new_content = (
        content[:insert_position] + 
        register_callback_method + 
        content[insert_position:]
    )
    
    # Write the updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Successfully added register_callback method to TrulyUnifiedCallbacks!")
    return True

if __name__ == "__main__":
    success = add_register_callback_method()
    if success:
        print("\n🚀 Now test your app: python3 app.py")
    else:
        print("\n❌ Fix failed - manual intervention required")