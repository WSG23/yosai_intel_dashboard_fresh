"""Compatibility shim for legacy ``intel_analysis_service`` imports.

This module re-exports the canonical package located at
``services/intel_analysis_service/src/intel_analysis_service`` so existing
imports continue to function. The shim will be removed in a future release.
"""

from services.intel_analysis_service.src.intel_analysis_service import *  # noqa: F401,F403
