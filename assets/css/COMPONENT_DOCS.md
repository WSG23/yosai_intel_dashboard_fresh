# Yōsai Intel CSS Component Documentation

Design tokens in `01-foundation/_variables.css` establish a consistent spacing
scale, border radius and shadow system modeled after Apple's Human Interface
Guidelines. All components rely on these custom properties to ensure uniform
metrics across the dashboard.

## Component Library


### Panels Component

**File:** `03-components/_panels.css`

**Usage:**
```html
<!-- Basic usage -->
<div class="panels">Panels Content</div>

<!-- With modifiers -->
<div class="panels panels--variant">Panels Variant</div>
```

**Available Variants:**
- `panels--primary`
- `panels--secondary`
- `panels--small`
- `panels--large`

---

### Alerts Component

**File:** `03-components/_alerts.css`

**Usage:**
```html
<!-- Basic usage -->
<div class="alerts">Alerts Content</div>

<!-- With modifiers -->
<div class="alerts alerts--variant">Alerts Variant</div>
```

**Available Variants:**
- `alerts--primary`
- `alerts--secondary`
- `alerts--small`
- `alerts--large`

---

### Cards Component

**File:** `03-components/_cards.css`

**Usage:**
```html
<!-- Basic usage -->
<div class="cards">Cards Content</div>

<!-- With modifiers -->
<div class="cards cards--variant">Cards Variant</div>
```

**Available Variants:**
- `cards--primary`
- `cards--secondary`
- `cards--small`
- `cards--large`

---

### Navigation Component

**File:** `03-components/_navigation.css`

**Usage:**
```html
<!-- Basic usage -->
<div class="navigation">Navigation Content</div>

<!-- With modifiers -->
<div class="navigation navigation--variant">Navigation Variant</div>
```

**Available Variants:**
- `navigation--primary`
- `navigation--secondary`
- `navigation--small`
- `navigation--large`

---

### Buttons Component

**File:** `03-components/_buttons.css`

**Usage:**
```html
<!-- Basic usage -->
<div class="buttons">Buttons Content</div>

<!-- With modifiers -->
<div class="buttons buttons--variant">Buttons Variant</div>
```

**Available Variants:**
- `buttons--primary`
- `buttons--secondary`
- `buttons--small`
- `buttons--large`

---

### Chips Component

**File:** `03-components/_chips.css`

**Usage:**
```html
<!-- Basic usage -->
<div class="chips">Chips Content</div>

<!-- With modifiers -->
<div class="chips chips--variant">Chips Variant</div>
```

**Available Variants:**
- `chips--primary`
- `chips--secondary`
- `chips--small`
- `chips--large`
- `chip--gold` – uses a gradient with `--color-warning` to remain readable

When customizing colors, ensure a minimum contrast ratio of 4.5:1 for text within chips.

---

### Navbar Component

**File:** `components/ui/navbar.py`

The navigation bar consolidates common links and the theme toggle into a shared
component. Below is a minimal Dash example using the `create_navbar_layout`
factory. In development you can preview components interactively using a
Storybook-style setup with `dash`:

```python
from dash import Dash, html
from components.ui.navbar import create_navbar_layout

app = Dash(__name__)
app.layout = html.Div([
    create_navbar_layout(),
    html.Div("Preview Area", className="p-4")
])

if __name__ == "__main__":
    app.run_server(debug=True)
```

The navbar respects the design tokens defined in `_variables.css` for spacing,
rounded corners and shadows to match Apple-style metrics.

---
