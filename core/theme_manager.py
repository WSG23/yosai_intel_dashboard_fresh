"""Theme management utilities for the dashboard."""

from __future__ import annotations

import logging
from typing import Set

from core.unicode import sanitize_unicode_input

logger = logging.getLogger(__name__)

DEFAULT_THEME = "dark"
ALLOWED_THEMES: Set[str] = {"dark", "light", "high-contrast"}


def sanitize_theme(theme: str | None) -> str:
    """Sanitize and validate the provided theme string."""
    cleaned = sanitize_unicode_input(theme or "").lower()
    if cleaned in ALLOWED_THEMES:
        return cleaned
    logger.debug(f"Invalid theme '{theme}', falling back to '{DEFAULT_THEME}'")
    return DEFAULT_THEME


def generate_theme_script() -> str:
    """Return a script snippet that applies the saved theme early."""
    allowed_list = ",".join(f"'{t}'" for t in ALLOWED_THEMES)
    script = f"""
    <script>
    (function() {{
        const DEFAULT_THEME = '{DEFAULT_THEME}';
        const ALLOWED_THEMES = new Set([{allowed_list}]);
        function sanitize(theme) {{
            theme = (theme || '').toString().toLowerCase();
            return ALLOWED_THEMES.has(theme) ? theme : DEFAULT_THEME;
        }}
        const saved = sanitize(localStorage.getItem('app-theme'));
        const system = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        const initial = saved || sanitize(system);

        function applyTheme(theme) {{
            const clean = sanitize(theme);
            const html = document.documentElement;
            html.classList.remove('light-mode', 'dark-mode', 'high-contrast-mode');
            const classMap = {{ 'dark': 'dark-mode', 'light': 'light-mode', 'high-contrast': 'high-contrast-mode' }};
            html.classList.add(classMap[clean] || 'dark-mode');
            localStorage.setItem('app-theme', clean);
            document.dispatchEvent(new CustomEvent('themeChange', {{ detail: clean }}));
        }}

        if (document.readyState !== 'loading') {{
            applyTheme(initial);
        }} else {{
            document.addEventListener('DOMContentLoaded', function(){{ applyTheme(initial); }});
        }}

        window.setAppTheme = applyTheme;
    }})();
    </script>
    """
    return script


def apply_theme_settings(app) -> None:
    """Patch ``app.index_string`` to inject the theme management script."""
    try:
        snippet = generate_theme_script()
        marker = "{%css%}"
        if hasattr(app, "index_string") and app.index_string:
            if marker in app.index_string:
                app.index_string = app.index_string.replace(
                    marker, snippet + "\n    " + marker
                )
            else:
                app.index_string = snippet + app.index_string
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning(f"Failed to apply theme settings: {exc}")
