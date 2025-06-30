#!/usr/bin/env python3
"""
Simplified Models Package
"""

# Import core models only
from .enums import (
    AnomalyType, AccessResult, BadgeStatus,
    SeverityLevel, TicketStatus, DoorType, AccessType
)

from .entities import Person, Door, Facility
from .events import AccessEvent, AnomalyDetection, IncidentTicket
from services.registry import get_service

BaseModel = get_service("BaseModel")
AccessEventModel = get_service("AccessEventModel")
AnomalyDetectionModel = get_service("AnomalyDetectionModel")
ModelFactory = get_service("ModelFactory")
BASE_MODELS_AVAILABLE = BaseModel is not None

__all__ = [
    'AnomalyType', 'AccessResult', 'BadgeStatus', 'SeverityLevel',
    'TicketStatus', 'DoorType', 'AccessType', 'Person', 'Door', 'Facility',
    'AccessEvent', 'AnomalyDetection', 'IncidentTicket',
    'BaseModel', 'AccessEventModel', 'AnomalyDetectionModel', 'ModelFactory',
    'BASE_MODELS_AVAILABLE'
]
