#!/usr/bin/env python3
"""
Simplified Models Package
"""

# Import core models only
from .enums import (
    AnomalyType, AccessResult, BadgeStatus, 
    SeverityLevel, TicketStatus, DoorType
)

from .entities import Person, Door, Facility
from .events import AccessEvent, AnomalyDetection, IncidentTicket

try:
    from .base import BaseModel, AccessEventModel, AnomalyDetectionModel, ModelFactory
    BASE_MODELS_AVAILABLE = True
except ImportError:
    BASE_MODELS_AVAILABLE = False
    BaseModel = None
    AccessEventModel = None
    AnomalyDetectionModel = None
    ModelFactory = None

__all__ = [
    'AnomalyType', 'AccessResult', 'BadgeStatus', 'SeverityLevel',
    'TicketStatus', 'DoorType', 'Person', 'Door', 'Facility',
    'AccessEvent', 'AnomalyDetection', 'IncidentTicket',
    'BaseModel', 'AccessEventModel', 'AnomalyDetectionModel', 'ModelFactory',
    'BASE_MODELS_AVAILABLE'
]
