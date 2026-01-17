from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AI Surveillance Sensor Frame API")

class SensorFrame(BaseModel):
    frame_id: int
    timestamp_ms: int
    flame: int
    mq135_raw: int
    thermal: list[float]

@app.post("/sensor-frame")
def receive_sensor_frame(frame: SensorFrame):
    print("RECEIVED:", frame.frame_id)
    return {"status": "ok"}
