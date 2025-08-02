# New Dashboard Migration

The original dashboard interface served from `yosai_intel_dashboard` has been replaced with the redesigned React frontend in `ui/`.

## Legacy Usage

```html
<!-- templates/dashboard.html -->
{% extends "base.html" %}
{% block content %}
  <h1>Legacy Dashboard</h1>
{% endblock %}
```

## New Usage

```javascript
import { createRoot } from 'react-dom/client';
import Dashboard from './Dashboard';

const root = createRoot(document.getElementById('root'));
root.render(<Dashboard />);
```

## Caveats

- Requires Node.js 18+ and npm 9+ for building assets.
- Custom Jinja plugins must be reimplemented as React components.
- Server-side rendering from the legacy system is no longer available.

## Migration Steps

1. Update deployment pipelines to build the React assets using `npm run build`.
2. Serve the compiled files from the `ui/dist` directory.
3. Remove references to the legacy Jinja templates and associated routes.

Refer to the [Deprecation Timeline](../deprecation_timeline.md) for key dates.
