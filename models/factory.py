# Fix 1: Create models/factory.py
# Save this as: models/factory.py

"""
Factory classes for creating model instances
"""

class ModelFactory:
    """Factory class for creating data model instances"""
    
    @staticmethod
    def create_access_model(data_source):
        """Create an AccessEventModel instance"""
        # For now, just return a placeholder
        # This will be fully implemented when you add database connections
        return f"AccessEventModel with {data_source}"
    
    @staticmethod
    def create_anomaly_model(data_source):
        """Create an AnomalyDetectionModel instance"""
        return f"AnomalyDetectionModel with {data_source}"
    
    @staticmethod
    def create_all_models(data_source):
        """Create all standard models with a single data source"""
        return {
            'access': ModelFactory.create_access_model(data_source),
            'anomaly': ModelFactory.create_anomaly_model(data_source)
        }

# Fix 2: Update models/__init__.py
# Replace your current models/__init__.py with this:

"""
Yōsai Intel Data Models Package
"""

# Import enums
from .enums import (
    AnomalyType,
    AccessResult, 
    BadgeStatus,
    SeverityLevel,
    TicketStatus,
    DoorType
)

# Import entities  
from .entities import (
    Person,
    Door, 
    Facility
)

# Import events
from .events import (
    AccessEvent,
    AnomalyDetection,
    IncidentTicket
)

# Import factory
from .factory import ModelFactory

# Define what gets exported
__all__ = [
    # Enums
    'AnomalyType', 'AccessResult', 'BadgeStatus', 'SeverityLevel', 
    'TicketStatus', 'DoorType',
    
    # Entities
    'Person', 'Door', 'Facility',
    
    # Events
    'AccessEvent', 'AnomalyDetection', 'IncidentTicket',
    
    # Factory
    'ModelFactory'
]