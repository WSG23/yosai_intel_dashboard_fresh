"""
GDPR/APPI Compliance Plugin for Yōsai Intel Dashboard
"""

from .plugin import CompliancePlugin

__version__ = "1.0.0"
__plugin_name__ = "compliance_plugin"
__description__ = "GDPR/APPI compliance framework"

def create_plugin():
    """Plugin entry point"""
    return CompliancePlugin()