from fastapi import FastAPI
from backend.modules.alerts_engine import evaluate_alerts

app = FastAPI()

latest_alert = None

@app.post("/alerts/evaluate")
def evaluate(payload: dict):
    global latest_alert

    sensor_data = payload["sensor"]
    vision_data = payload["vision"]

    alert = evaluate_alerts(sensor_data, vision_data)

    if alert:
        latest_alert = alert
        return {"status": "ALERT", "alert": alert}

    return {"status": "OK"}

@app.get("/alerts/latest")
def get_latest():
    return latest_alert or {"status": "NO_ALERT"}
