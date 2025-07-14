# Add navbar callback registration to app factory
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Add navbar callback registration after manual routing
old_section = '''        # Register manual routing
        from pages import create_manual_router
        create_manual_router(app)'''

new_section = '''        # Register manual routing
        from pages import create_manual_router
        create_manual_router(app)
        
        # Register navbar callbacks
        try:
            from components.ui.navbar import register_navbar_callbacks
            register_navbar_callbacks(app)
            logger.info("✅ Navbar callbacks registered")
        except Exception as e:
            logger.warning(f"⚠️ Navbar callbacks failed: {e}")'''

content = content.replace(old_section, new_section)

with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)

print("✅ Added navbar callback registration")
