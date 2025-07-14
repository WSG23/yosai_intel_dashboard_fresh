#!/usr/bin/env python3
"""Minimal test for app factory."""

from core.app_factory import create_app

# Create app using app factory
app = create_app()

if __name__ == "__main__":
    app.run_server(debug=True, port=8052)
