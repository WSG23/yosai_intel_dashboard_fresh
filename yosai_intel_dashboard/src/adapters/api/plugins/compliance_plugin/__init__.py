#!/usr/bin/env python3
"""
GDPR/APPI Compliance Plugin for Yōsai Intel Dashboard

A complete compliance framework implemented as a plugin that can be
enabled/disabled independently from the core application.
"""

from __future__ import annotations

__version__ = "1.0.0"
__plugin_name__ = "compliance_plugin"
__description__ = "GDPR/APPI compliance framework with consent management, DSAR processing, and audit logging"


# Plugin entry point
def create_plugin():
    """Create and return the compliance plugin instance"""
    from .plugin import CompliancePlugin

    return CompliancePlugin()
