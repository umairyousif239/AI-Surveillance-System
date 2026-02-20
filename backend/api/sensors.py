from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List
import threading

from backend.api.login import get_current_user

router = APIRouter(prefix="/sensors", tags=["Sensors"])

latest_frame = None
lock = threading.Lock()

class SensorFrame(BaseModel):
    frame_id: int
    timestamp_ms: int
    flame: int
    mq135_raw: int
    thermal: List[float] = Field(..., min_length=64, max_length=64)

@router.post("/sensor-frame")
def receive_sensor_frame(frame: SensorFrame):
    global latest_frame
    with lock:
        latest_frame = frame.dict()
    return {"status": "ok"}

@router.get("/latest", dependencies=[Depends(get_current_user)])
def get_latest():
    with lock:
        if latest_frame is None:
            return {"status": "no_data"}
        return latest_frame