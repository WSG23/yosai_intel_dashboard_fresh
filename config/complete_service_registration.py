"""Compatibility wrapper for application service registration."""

from __future__ import annotations

from startup.service_registration import (
    register_all_application_services,
    register_all_services,
    register_core_infrastructure,
    register_analytics_services,
    register_security_services,
    register_export_services,
    register_learning_services,
)

__all__ = [
    "register_all_application_services",
    "register_all_services",
    "register_core_infrastructure",
    "register_analytics_services",
    "register_security_services",
    "register_export_services",
    "register_learning_services",
]
