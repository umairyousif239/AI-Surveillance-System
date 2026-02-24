import time
import requests
from enum import Enum
from typing import Optional

from backend.api.vision import get_latest as fetch_latest_vision
from backend.api.sensors import get_latest as fetch_latest_sensors

from backend.modules.alert_state import AlertStatus, AlertSeverity

from backend.modules.alert_config import (
    VISION_FIRE_CONF,
    MQ135_SMOKE_RAW,
    THERMAL_FIRE_TEMP,
    THERMAL_DELTA,
    FLAME_DETECTED
)

# Global Alert Memory
current_alert = None
last_trigger_time = 0
PERSISTENCE_SECONDS = 5 #Alert must persist to ensure its not a false positive
RESOLVE_TIMEOUT = 10 # Seconds without trigger results in resolved status

# Rate of Rise Memory
last_max_temp_val = None
last_temp_time_val = None

# Scoring Functions
def compute_confidence(
    fire: bool,
    smoke: bool,
    flame: bool,
    thermal_fire: bool,
    thermal_spike: bool
) -> float:
    
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

    global current_alert, last_trigger_time, last_max_temp_val, last_temp_time_val

    vision = fetch_latest_vision()
    sensors = fetch_latest_sensors()

    now = time.time()
    timestamp_ms = int(now * 1000)

    if not vision or not sensors:
        return None

    # -----------------------------
    # Vision Parsing (FIXED)
    # -----------------------------
    fire_detected = (
        vision.get("detected", False)
        and vision.get("confidence", 0) >= VISION_FIRE_CONF
    )

    # -----------------------------
    # Sensor Parsing
    # -----------------------------
    flame = sensors.get("flame", 0)
    mq135 = sensors.get("mq135_raw", 0)
    thermal = sensors.get("thermal", [])

    if not thermal:
        return None

    max_temp = max(thermal)
    min_temp = min(thermal)
    delta_temp = max_temp - min_temp
    
    # Rate of Rise Math
    thermal_ror = False
    if last_max_temp_val is not None and last_temp_time_val is not None:
        dt = max_temp - last_max_temp_val
        time_diff = now - last_temp_time_val
        
        if time_diff > 0:
            rate_of_rise = dt / time_diff
            # Trigger if temp jumps more than 2.0 celsius per second
            if rate_of_rise > 2.0:
                thermal_ror = True
                print(f"Rate of Rise SPIKE DETECTED: +{rate_of_rise:.1f}°C/s")
                
    # save the current state for the next frame's math
    last_max_temp_val = max_temp
    last_temp_time_val = now

    smoke_detected = mq135 >= MQ135_SMOKE_RAW
    flame_detected = flame == FLAME_DETECTED
    thermal_fire = max_temp >= THERMAL_FIRE_TEMP
    thermal_spike = delta_temp >= THERMAL_DELTA

    # -----------------------------
    # Source Labeling
    # -----------------------------
    if fire_detected and (smoke_detected or flame_detected or thermal_fire):
        source = "FUSED"
    elif fire_detected:
        source = "VISION_ONLY"
    elif smoke_detected or flame_detected or thermal_fire or thermal_ror:
        source = "SENSOR_ONLY"
    else:
        source = "UNKNOWN"

    # -----------------------------
    # Trigger Logic
    # -----------------------------
    trigger = (
        fire_detected and (smoke_detected or flame_detected or thermal_fire or thermal_ror)
    ) or (
        smoke_detected and (thermal_spike or thermal_ror)
    ) or (
        thermal_ror
    ) or (
        smoke_detected
    )

    # -----------------------------
    # No Trigger → Possibly Resolve
    # -----------------------------
    if not trigger:
        if current_alert and (now - last_trigger_time) > RESOLVE_TIMEOUT:
            current_alert["status"] = AlertStatus.RESOLVED
            current_alert["resolved_at"] = timestamp_ms
            resolved = current_alert
            current_alert = None
            return resolved
        return None

    # -----------------------------
    # Trigger Active
    # -----------------------------
    confidence = compute_confidence(
        fire_detected,
        smoke_detected,
        flame_detected,
        thermal_fire,
        thermal_spike,
    )

    severity = compute_severity(confidence)

    # -----------------------------
    # Create New Alert
    # -----------------------------
    if current_alert is None:
        current_alert = {
            "id": f"alert_{int(now)}",
            "type": "FIRE" if fire_detected else "SMOKE",
            "source": source,
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
                "thermal_ror": thermal_ror,
            },
        }

        # Start persistence timer properly
        last_trigger_time = now

        return current_alert

    # -----------------------------
    # Update Existing Alert
    # -----------------------------

    # Promote NEW → ACTIVE after persistence window
# Promote NEW → ACTIVE after persistence window
    if current_alert["status"] == AlertStatus.NEW:
        created_time_sec = current_alert["created_at"] / 1000.0
        if (now - created_time_sec) >= PERSISTENCE_SECONDS:
            current_alert["status"] = AlertStatus.ACTIVE

    # Update running alert
    current_alert.update({
        "severity": severity,
        "confidence": confidence,
        "updated_at": timestamp_ms,
    })

    # Keep refreshing trigger timer while active
    last_trigger_time = now

    return current_alert
