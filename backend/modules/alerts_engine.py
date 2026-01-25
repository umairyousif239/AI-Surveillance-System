import time
import uuid
from backend.modules.alert_config import *

def evaluate_alerts(sensor_data, vision_data):
    """
    sensor_data:
      flame, mq135_raw, thermal_pixels

    vision_data:
      fire_conf, smoke_conf
    """

    triggers = []
    confidence = 0.0

    # ---- Vision ----
    if vision_data.get("fire_conf", 0) > VISION_FIRE_CONF:
        triggers.append("vision")
        confidence += vision_data["fire_conf"]

    # ---- Flame IR ----
    if sensor_data["flame"] == FLAME_DETECTED:
        triggers.append("flame")
        confidence += 0.4

    # ---- Gas ----
    if sensor_data["mq135_raw"] > MQ135_SMOKE_RAW:
        triggers.append("gas")
        confidence += 0.3

    # ---- Thermal ----
    thermal = sensor_data["thermal"]
    if max(thermal) > THERMAL_FIRE_TEMP:
        triggers.append("thermal")
        confidence += 0.4

    if len(triggers) >= 2:
        return {
            "alert_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "type": "FIRE",
            "severity": "HIGH" if confidence > 1.2 else "MEDIUM",
            "confidence": round(min(confidence, 1.0), 2),
            "sources": triggers,
            "frame_id": sensor_data["frame_id"]
        }

    return None
