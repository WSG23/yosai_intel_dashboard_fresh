# Replace basic navbar with original navbar component
with open('core/app_factory/__init__.py', 'r') as f:
    content = f.read()

# Find and replace the basic navbar section
old_navbar = '''        html.Nav([
            html.H3("🏯 Yōsai Dashboard", style={"color": "white", "padding": "15px", "margin": "0"}),
        ], style={"background": "#1f2937", "margin-bottom": "20px"}),'''

new_navbar = '''        # Original navbar component with icons
        create_navbar_layout(),'''

# Also add the import at the top of the layout function
content = content.replace(
    'def create_main_layout():',
    '''def create_main_layout():
    from components.ui.navbar import create_navbar_layout'''
)

content = content.replace(old_navbar, new_navbar)

with open('core/app_factory/__init__.py', 'w') as f:
    f.write(content)

print("✅ Added original navbar component")
