> **Note**: Import paths updated for clean architecture. Legacy imports are deprecated.

YŌSAI INTEL DASHBOARD - MODELS SECTION GUIDE
=====================================================

This guide explains what each file in the models/ directory does in plain English, 
and shows you exactly how to use them in your code.

OVERVIEW: What are "Models"?
-----------------------------
Think of models as the "data blueprint" for your security system. They define:
- What information we track (person names, door IDs, access times)
- How that information is structured (required fields, data types)
- How different pieces of information relate to each other

It's like having a standardized form for every type of security event, so everything 
is organized and consistent.


FILE-BY-FILE BREAKDOWN
======================

### <span aria-hidden="true">📋</span> models/enums.py - "The Dropdown Lists"
WHAT IT DOES:
This file defines all the fixed choices/options used throughout the system.
Like dropdown menus in a form - you can only pick from specific options.

CONTAINS:
- AnomalyType: Types of security problems (tailgating, odd hours, etc.)
- AccessResult: What happened (Granted, Denied, Timeout, Error)
- BadgeStatus: Badge condition (Valid, Invalid, Expired, Suspended)
- SeverityLevel: How serious is it (Low, Medium, High, Critical)
- TicketStatus: Current state of incidents (New, Open, Resolved, etc.)
- DoorType: What kind of door (Standard, Critical, Emergency, etc.)

HOW OTHER MODULES USE IT:
```python
# In analytics page - checking access results
from yosai_intel_dashboard.src.models.enums import AccessResult, AnomalyType

def analyze_failed_access(data):
    denied_events = data[data['access_result'] == AccessResult.DENIED.value]
    return f"Found {len(denied_events)} denied access attempts"

# In dashboard components - showing severity colors
from yosai_intel_dashboard.src.models.enums import SeverityLevel

def get_alert_color(severity_text):
    if severity_text == SeverityLevel.CRITICAL.value:
        return "red"
    elif severity_text == SeverityLevel.HIGH.value:
        return "orange"
    return "yellow"

# In incident response - updating ticket status
from yosai_intel_dashboard.src.models.enums import TicketStatus

def resolve_ticket(ticket_id, resolution_type):
    if resolution_type == "harmful":
        new_status = TicketStatus.RESOLVED_HARMFUL
    elif resolution_type == "normal":
        new_status = TicketStatus.RESOLVED_NORMAL
    # Update database with new_status.value
```


### <span aria-hidden="true">👤</span> models/entities.py - "The People, Places, and Things"
WHAT IT DOES:
Defines the main "things" in your security system - people, doors, and buildings.
These are like the nouns in your security story.

CONTAINS:
- Person: Employee or visitor info (ID, name, clearance level, risk score)
- Door: Access point details (location, type, required clearance)
- Facility: Building information (name, address, operating hours)

HOW OTHER MODULES USE IT:
```python
# In user management - creating new employees
from yosai_intel_dashboard.src.models.entities import Person

def add_new_employee(emp_data):
    new_person = Person(
        person_id=emp_data['id'],
        name=emp_data['name'],
        department=emp_data['dept'],
        clearance_level=emp_data['clearance'],
        access_groups=['general', 'building_a']
    )
    # Save to database using new_person.to_dict()
    return new_person

# In map panel - showing door information
from yosai_intel_dashboard.src.models.entities import Door
from yosai_intel_dashboard.src.models.enums import DoorType

def create_door_for_map(door_data):
    door = Door(
        door_id=door_data['id'],
        door_name=door_data['name'],
        facility_id="HQ_TOWER",
        area_id="LOBBY",
        door_type=DoorType.CRITICAL if door_data['is_critical'] else DoorType.STANDARD
    )
    return {
        'id': door.door_id,
        'name': door.door_name,
        'color': 'red' if door.is_critical else 'blue'
    }

# In analytics - calculating facility statistics
from yosai_intel_dashboard.src.models.entities import Facility

def get_facility_stats(facility_id):
    facility = Facility(
        facility_id=facility_id,
        facility_name="HQ Tower East",
        timezone="America/New_York"
    )
    # Use facility.timezone for time calculations
    # Use facility.operating_hours for business hours analysis
```


⚡ models/events.py - "The Things That Happen"
----------------------------------------------
WHAT IT DOES:
Defines the security events and incidents - the action verbs of your system.
Every time someone swipes a badge, an anomaly is detected, or a ticket is created.

CONTAINS:
- AccessEvent: Someone tried to access a door (successful or failed)
- AnomalyDetection: AI found something suspicious
- IncidentTicket: A security incident that needs human attention

HOW OTHER MODULES USE IT:
```python
# In file upload processing - converting CSV to structured events
from yosai_intel_dashboard.src.models.events import AccessEvent
from yosai_intel_dashboard.src.models.enums import AccessResult, BadgeStatus

def process_access_log_csv(csv_data):
    events = []
    for row in csv_data.iterrows():
        event = AccessEvent(
            event_id=f"EVT_{row['id']}",
            timestamp=pd.to_datetime(row['timestamp']),
            person_id=row['person_id'],
            door_id=row['door_id'],
            access_result=AccessResult(row['result']),
            badge_status=BadgeStatus(row['badge_status'])
        )
        events.append(event)
    return events

# In anomaly detection - creating anomaly records
from yosai_intel_dashboard.src.models.events import AnomalyDetection
from yosai_intel_dashboard.src.core.domain.entities.enums import AnomalyType, SeverityLevel

def flag_odd_time_access(access_event):
    anomaly = AnomalyDetection(
        anomaly_id=f"ANOM_{uuid.uuid4()}",
        event_id=access_event.event_id,
        anomaly_type=AnomalyType.ODD_TIME,
        severity=SeverityLevel.MEDIUM,
        confidence_score=0.85,
        description=f"Access at {access_event.timestamp} outside normal hours",
        detected_at=datetime.now()
    )
    return anomaly

# In incident management - creating tickets
from yosai_intel_dashboard.src.core.domain.entities.events import IncidentTicket
from yosai_intel_dashboard.src.core.domain.entities.enums import TicketStatus

def create_security_ticket(anomaly, threat_level):
    ticket = IncidentTicket(
        ticket_id=f"TKT_{uuid.uuid4()}",
        event_id=anomaly.event_id,
        anomaly_id=anomaly.anomaly_id,
        status=TicketStatus.NEW,
        threat_score=threat_level,
        facility_location="HQ Tower East",
        area="Server Room"
    )
    return ticket
```
### <span aria-hidden="true">🏗️</span> models/base.py - "The Foundation Rules"
Sets up the basic rules that all data access models must follow.
Like a contract that says "every model must be able to get data and validate it."

CONTAINS:
- BaseDataModel: The blueprint that all other data models inherit from

HOW OTHER MODULES USE IT:
```python
# When creating new data models - inherit from BaseDataModel
from yosai_intel_dashboard.src.core.domain.entities.base import BaseDataModel

class PersonModel(BaseDataModel):
    def get_data(self, filters=None):
        # Must implement: how to get person data from yosai_intel_dashboard.src.database
        query = "SELECT * FROM people"
        if filters and 'department' in filters:
            query += f" WHERE department = '{filters['department']}'"
        return self.db.execute_query(query)
    
    def get_summary_stats(self):
        # Must implement: summary statistics
        return {
            'total_people': self.get_data().shape[0],
            'departments': self.get_data()['department'].nunique()
        }
    
    def validate_data(self, data):
        # Must implement: data validation
        required_cols = ['person_id', 'name']
        return all(col in data.columns for col in required_cols)

# In services - using the standard interface
def get_model_summary(model: BaseDataModel):
    # Works with ANY model that inherits from BaseDataModel
    return model.get_summary_stats()
```


### <span aria-hidden="true">📊</span> models/access_event.py - "The Door Activity Tracker"
WHAT IT DOES:
Handles all database operations for access control events. When someone swipes 
their badge, this model helps you find, filter, and analyze that data.

HOW OTHER MODULES USE IT:
```python
# In dashboard - getting recent activity
from yosai_intel_dashboard.src.core.domain.entities.access_event import AccessEventModel

def update_live_feed(db_connection):
    access_model = AccessEventModel(db_connection)
    recent_events = access_model.get_recent_events(hours=2)
    
    # Convert to display format
    feed_items = []
    for _, event in recent_events.iterrows():
        feed_items.append({
            'time': event['timestamp'],
            'person': event['person_id'],
            'door': event['door_id'],
            'result': event['access_result'],
            'color': 'green' if event['access_result'] == 'Granted' else 'red'
        })
    return feed_items

# In analytics - trend analysis
def generate_monthly_report(db_connection):
    access_model = AccessEventModel(db_connection)
    trends = access_model.get_trend_analysis(days=30)
    
    # Use for charts
    chart_data = {
        'dates': trends['date'].tolist(),
        'total_events': trends['total_events'].tolist(),
        'granted_events': trends['granted_events'].tolist()
    }
    return chart_data

# In search functionality
def search_person_activity(db_connection, person_id, start_date):
    access_model = AccessEventModel(db_connection)
    filters = {
        'person_id': person_id,
        'start_date': start_date
    }
    events = access_model.get_data(filters)
    return events
```



### <span aria-hidden="true">🚨</span> AnomalyDetectionModel - "The Threat Detector"
WHAT IT DOES:
Tracks suspicious activity and anomalies detected by AI. The model lives in
`models/base.py` and can be imported directly from the `models` package.

HOW OTHER MODULES USE IT:
```python
# In dashboard - showing current threats
from yosai_intel_dashboard.src.core.domain.entities import AnomalyDetectionModel

def get_active_threats(db_connection, events):
    anomaly_model = AnomalyDetectionModel(db_connection)

    high_severity = [
        a for a in anomaly_model.detect_anomalies(events)
        if a.get('severity') == 'high'
    ]
    return high_severity
```
