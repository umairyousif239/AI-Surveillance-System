from enum import Enum
from uuid import uuid4
import time

class AlertState(str, Enum):
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"

class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class Alert:
    def __init__(self, alert_type, severity, confidence, sources):
        self.alert_id = str(uuid4())
        self.type = alert_type
        self.severity = severity
        self.confidence = confidence
        self.sources = sources
        self.state = AlertState.PENDING
        self.created_at = int(time.time() * 1000)
        self.last_updated = self.created_at
    
    def activate(self):
        self.state = AlertState.ACTIVE
        self.last_updated = int(time.time() * 1000)
    
    def resolve(self):
        self.state = AlertState.RESOLVED
        self.last_updated = int(time.time() * 1000)