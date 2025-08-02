#!/usr/bin/env python3
"""Utility to inspect available methods on a Dash app object."""
from typing import Any


def debug_dash_object(app: Any) -> None:
    print(f"App type: {type(app)}")
    print(f"App class: {app.__class__}")

    callback_methods = [attr for attr in dir(app) if "callback" in attr.lower()]
    print(f"Available callback methods: {callback_methods}")

    wrapper_attrs = []
    for attr in ["_unified_wrapper", "_callback_registry", "_yosai_container"]:
        if hasattr(app, attr):
            wrapper_attrs.append(attr)
    print(f"Wrapper attributes: {wrapper_attrs}")


if __name__ == "__main__":
    from yosai_intel_dashboard.src.core.app_factory import create_app

    app = create_app(mode="simple")
    debug_dash_object(app)
