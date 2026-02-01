import time
import requests
import enum as Enum
from typing import Optional

from backend.modules.alert_config import (
    VISION_FIRE_CONF,
    MQ135_SMOKE_RAW,
    THERMAL_FIRE_TEMP,
    THERMAL_DELTA,
    FLAME_DETECTED
)

# Internal API Endpoints
VISION_URL = "http://127.0.0.1:8000/vision/detections/latest"
SENSORS_URL = "http://127.0.0.1:8000/sensors/latest"
REQUEST_TIMEOUT = 0.25

#Alert State & Severity
class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AlertStatus(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"

# Global Alert Memory
current_alert = None
last_trigger_time = 0
PERSISTENCE_SECONDS = 5 #Alert must persist to ensure its not a false positive
RESOLVE_TIMEOUT = 10 # Seconds without trigger results in resolved status

# Data Fetching
def fetch_latest_vision():
    try:
        r = requests.get(VISION_URL, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def fetch_latest_sensors():
    try:
        r = requests.get(SENSORS_URL, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

# Scoring Functions
def compute_confidence(fire, smoke, flame, thermal_fire, thermal_spike):
    score = 0.0
    if fire:
        score += 0.4
    if smoke:
        score += 0.2
    if flame:
        score += 0.2
    if thermal_fire:
        score += 0.1
    if thermal_spike:
        score += 0.1
    return round(min(score, 1.0), 2)

def compute_severity(confidence):
    if confidence >= 0.75:
        return AlertSeverity.HIGH
    if confidence >= 0.45:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW

# Core Evaluation Logic
def evaluate_alerts() -> Optional[dict]:
    """
    Pulls latest sensor and vision data
    Evaluates alert conditions
    Manages alert lifecycle
    """
    
    global current_alert, last_trigger_time
    
    vision = fetch_latest_vision()
    sensors = fetch_latest_sensors()
    
    now = time.time()
    timestamp_ms = int(now * 1000)
    
    if not vision or not sensors:
        return None
    
    detections = vision.get("detections", [])
    flame = sensors.get("flame", 0)
    mq135 = sensors.get("mq135_raw", 0)
    thermal = sensors.get("thermal", [])
    
    if not thermal:
        return None
    
    max_temp = max(thermal)
    min_temp = min(thermal)
    delta_temp = max_temp - min_temp
    
    # Signal Extraction
    fire_detected = any(
        d["class"] == "fire" and d["confidence"] >= VISION_FIRE_CONF
        for d in detections
    )
    
    smoke_detected = mq135 >= MQ135_SMOKE_RAW
    flame_detected = flame == FLAME_DETECTED
    thermal_fire = max_temp >= THERMAL_FIRE_TEMP
    thermal_spike = delta_temp >= THERMAL_DELTA
    
    # Decision Gate
    trigger = (
        fire_detected and (smoke_detected or flame_detected or thermal_fire)
    ) or (
        smoke_detected and thermal_spike
    )
    
    if not trigger:
        # Resolve Logic
        if current_alert and (now - last_trigger_time) > RESOLVE_TIMEOUT:
            current_alert["status"] = AlertStatus.RESOLVED
            current_alert["resolved_at"] = timestamp_ms
            resolved = current_alert
            current_alert = None
            return resolved
        return None
    
    last_trigger_time = now
    
    confidence = compute_confidence(
        fire_detected,
        smoke_detected,
        flame_detected,
        thermal_fire,
        thermal_spike,
    )
    
    severity = compute_severity(confidence)
    
    # Alert or Update Alerts
    if current_alert is None:
        current_alert = {
            "id": f"alert_{int(now)}",
            "type": "FIRE" if fire_detected else "SMOKE",
            "status": AlertStatus.NEW,
            "severity": severity,
            "confidence": confidence,
            "created_at": timestamp_ms,
            "signals": {
                "vision_fire": fire_detected,
                "smoke": smoke_detected,
                "flame": flame_detected,
                "max_temp": round(max_temp, 1),
                "delta_temp": round(delta_temp, 1),
                "mq135_raw": mq135,
            },
        }
        return current_alert
    
    # Promoting NEW alert to ACTIVE alert if it fulfills the persistence time
    if current_alert["status"] == AlertStatus.NEW:
        if (now - last_trigger_time) >= PERSISTENCE_SECONDS:
            current_alert["status"] = AlertStatus.ACTIVE
    
    # Update the running alerts
    current_alert.update({
        "severity": severity,
        "confidence": confidence,
        "updated_at": timestamp_ms,
    })
    
    return current_alert