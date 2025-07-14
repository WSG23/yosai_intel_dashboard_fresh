# Add navbar callbacks to minimal app
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Add navbar callback registration after routing
addition = '''
        
        # Register navbar callbacks
        try:
            from components.ui.navbar import register_navbar_callbacks
            register_navbar_callbacks(app)
        except Exception as e:
            logger.warning(f"Navbar callbacks failed: {e}")'''

# Insert after the manual router registration
content = content.replace(
    'create_manual_router(app)',
    'create_manual_router(app)' + addition
)

with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)

print("✅ Added navbar callbacks")
