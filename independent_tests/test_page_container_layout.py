import re

from dash import dcc, html, page_container

# Dynamically load the _create_main_layout function without importing the whole module
with open('core/app_factory/__init__.py') as f:
    src = f.read()

start_idx = src.find('def _create_main_layout')
end_idx = src.find('def _create_navbar')
func_code = src[start_idx:end_idx]

namespace = {
    'html': html,
    'dcc': dcc,
    'page_container': page_container,
    '_create_navbar': lambda: html.Div('nav'),
    'DEFAULT_THEME': 'dark',
}
exec(func_code, namespace)


def test_page_container_in_layout():
    layout = namespace['_create_main_layout']()
    assert 'page_container' in str(layout)
