"""Dependency injection helper utilities.

This module re-exports the most commonly used decorators from
:mod:`core.di.decorators` to provide a single import location for
applications.
"""

from .decorators import injectable, inject, singleton, transient

__all__ = ["injectable", "inject", "singleton", "transient"]
