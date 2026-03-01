import cv2
import time
import asyncio
import numpy as np
import os
from multiprocessing import Process, Manager, shared_memory
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.api.login import get_current_user, get_current_user_from_query

# --- Shared Memory Configurations (720p) ---
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FRAME_CHANNELS = 3
FRAME_BYTES = FRAME_WIDTH * FRAME_HEIGHT * FRAME_CHANNELS
SHM_NAME = "vision_frame_shm"

# --- Global IPC Variables ---
vision_manager = None
shared_dict = None
frame_lock = None
vision_process = None
shm_read = None

# ==========================================
# PROCESS 2: THE ISOLATED YOLO WORKER
# ==========================================
def capture_loop(shared_dict, lock):
    """Isolated process to handle camera and AI inference"""
    
    # Core Pinning: Move this process to Core 3 immediately
    try:
        os.sched_setaffinity(0, {3}) 
        print("DEBUG: YOLO Process successfully pinned to CPU Core 3")
    except Exception as e:
        print(f"DEBUG: Core pinning failed (usually requires Linux): {e}")

    from ultralytics import YOLO
    model = YOLO("models/yolov8n_ncnn_model", task="detect")
    IMG_SIZE = 256
    CONF_THRESH = 0.25

    # Allocate Shared Memory
    try:
        shm = shared_memory.SharedMemory(name=SHM_NAME, create=True, size=FRAME_BYTES)
    except FileExistsError:
        shm = shared_memory.SharedMemory(name=SHM_NAME, create=False)

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")

    frame_id = 0
    prev_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            
            try:
                results = model.predict(frame, imgsz=IMG_SIZE, conf=CONF_THRESH, device="cpu", verbose=False)
                r = results[0]
                detections = []

                if r.boxes is not None:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        detections.append({
                            "class": model.names[cls_id],
                            "confidence": round(conf, 3),
                            "bbox": [x1, y1, x2, y2]
                        })

                annotated_frame = r.plot()
            except Exception:
                annotated_frame = frame

            # Calculate FPS for the overlay
            curr_time = time.time()
            fps = 1 / max(curr_time - prev_time, 1e-5)
            prev_time = curr_time
            cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

            # Update shared dictionary for API
            with lock:
                shared_dict["latest_detections"] = {
                    "frame_id": frame_id,
                    "timestamp_ms": int(time.time() * 1000),
                    "detections": detections
                }
            
            # Zero-Copy Write to Shared Memory
            shm.buf[:FRAME_BYTES] = annotated_frame.tobytes()
            frame_id = (frame_id + 1) % 1_000_000

    finally:
        cap.release()
        shm.close()

# ==========================================
# PROCESS 1: FASTAPI LIFECYCLE MANAGERS
# ==========================================
def start_vision():
    global vision_manager, shared_dict, frame_lock, vision_process, shm_read
    
    vision_manager = Manager()
    shared_dict = vision_manager.dict()
    shared_dict["latest_detections"] = None
    frame_lock = vision_manager.Lock()

    # Clear stale memory from previous crashes
    try:
        temp_shm = shared_memory.SharedMemory(name=SHM_NAME)
        temp_shm.close()
        temp_shm.unlink()
    except FileNotFoundError:
        pass

    vision_process = Process(target=capture_loop, args=(shared_dict, frame_lock), daemon=True)
    vision_process.start()

    # Retry connection to Shared Memory (Wait for YOLO to boot)
    connected = False
    for i in range(15): 
        try:
            time.sleep(1)
            shm_read = shared_memory.SharedMemory(name=SHM_NAME, create=False)
            connected = True
            print(f"✅ FastAPI connected to Shared Memory on attempt {i+1}")
            break
        except FileNotFoundError:
            print(f"Waiting for YOLO... (Attempt {i+1}/15)")
    
    if not connected:
        print("❌ CRITICAL: Shared Memory connection failed.")

def stop_vision():
    global vision_process, shm_read, vision_manager
    if vision_process and vision_process.is_alive():
        vision_process.terminate()
        vision_process.join()
    if shm_read:
        shm_read.close()
    if vision_manager:
        vision_manager.shutdown()

def get_current_frame():
    """Reads raw bytes from RAM. Returns a View, not a Copy."""
    global shm_read
    if not shm_read:
        return None
    try:
        # Create a zero-copy numpy view of the shared memory buffer
        return np.ndarray((FRAME_HEIGHT, FRAME_WIDTH, FRAME_CHANNELS), dtype=np.uint8, buffer=shm_read.buf)
    except:
        return None

def get_snapshot_frame():
    # Snapshots DO need a copy to prevent the next frame from overwriting it
    frame = get_current_frame()
    return frame.copy() if frame is not None else None

# ==========================================
# FASTAPI ROUTER & ENDPOINTS
# ==========================================
router = APIRouter(prefix="/vision", tags=["Vision"])

async def mjpeg_generator():
    while True:
        frame = get_current_frame()
        if frame is None:
            await asyncio.sleep(0.1)
            continue

        # Reduce JPEG quality to 50 for smoother 720p streaming on Pi
        ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
        if not ret:
            await asyncio.sleep(0.01)
            continue
        
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        
        # Cap stream to ~25 FPS to reduce Network I/O spikes
        await asyncio.sleep(0.04)

@router.get("/video_feed")
async def video_feed(username: str = Depends(get_current_user_from_query)):
    return StreamingResponse(mjpeg_generator(), media_type='multipart/x-mixed-replace; boundary=frame')

@router.get("/latest", dependencies=[Depends(get_current_user)])
def get_latest():
    with frame_lock:
        data = shared_dict.get("latest_detections")

    if not data:
        return {"detected": False, "fire_confidence": 0.0, "smoke_confidence": 0.0, "timestamp": None}

    detections = data["detections"]
    fire_conf = max([d["confidence"] for d in detections if d["class"].lower() == "fire"], default=0.0)
    smoke_conf = max([d["confidence"] for d in detections if d["class"].lower() == "smoke"], default=0.0)

    return {
        "detected": (fire_conf > 0 or smoke_conf > 0),
        "fire_confidence": fire_conf,
        "smoke_confidence": smoke_conf,
        "timestamp": data["timestamp_ms"]
    }