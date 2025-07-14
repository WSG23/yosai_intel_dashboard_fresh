from components.ui.navbar import create_navbar_layout
from dash import page_container, html, dcc

print("Testing components individually:")
print("1. Testing navbar:")
navbar_result = create_navbar_layout()
print(f"Navbar type: {type(navbar_result)}")
print(f"Navbar content: {str(navbar_result)[:200]}...")

print("\n2. Testing page_container:")
print(f"page_container type: {type(page_container)}")
print(f"page_container: {page_container}")
