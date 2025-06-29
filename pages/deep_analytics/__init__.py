"""Initialize the deep analytics page and expose callbacks."""

from .layout import layout
from .callbacks import register_callbacks  # noqa: F401
from .analysis import *  # noqa: F401,F403

__all__ = ["layout", "register_callbacks"]
