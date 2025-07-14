# Fix React style property warnings in navbar
with open('components/ui/navbar.py', 'r') as f:
    content = f.read()

# Convert CSS-style properties to React camelCase
css_to_react = {
    'margin-bottom': 'marginBottom',
    'margin-top': 'marginTop',
    'margin-left': 'marginLeft',
    'margin-right': 'marginRight',
    'padding-top': 'paddingTop',
    'padding-bottom': 'paddingBottom',
    'padding-left': 'paddingLeft',
    'padding-right': 'paddingRight',
    'background-color': 'backgroundColor',
    'font-size': 'fontSize',
    'font-weight': 'fontWeight',
    'text-align': 'textAlign',
    'text-decoration': 'textDecoration',
    'line-height': 'lineHeight'
}

for css_prop, react_prop in css_to_react.items():
    content = content.replace(f'"{css_prop}"', f'"{react_prop}"')
    content = content.replace(f"'{css_prop}'", f"'{react_prop}'")

with open('components/ui/navbar.py', 'w') as f:
    f.write(content)

print("✅ Fixed React style properties in navbar")
