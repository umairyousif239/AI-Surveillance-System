import cv2
import time
import asyncio
import numpy as np
from multiprocessing import Process, Manager, shared_memory
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.api.login import get_current_user, get_current_user_from_query

# --- Shared Memory Configurations ---
# We must lock the resolution so the RAM allocation byte-size is perfectly static
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FRAME_CHANNELS = 3
FRAME_BYTES = FRAME_WIDTH * FRAME_HEIGHT * FRAME_CHANNELS
SHM_NAME = "vision_frame_shm"

# --- Global IPC Variables for FastAPI ---
vision_manager = None
shared_dict = None
frame_lock = None
vision_process = None
shm_read = None

# ==========================================
# PROCESS 2: THE ISOLATED YOLO WORKER
# ==========================================
def capture_loop(shared_dict, lock):
    """This runs on a completely separate CPU core with its own Python GIL"""
    
    # IMPORTANT: The model MUST be imported and loaded inside the child process
    from ultralytics import YOLO
    model = YOLO("models/yolov8n_ncnn_model", task="detect")
    IMG_SIZE = 256
    CONF_THRESH = 0.25

    # 1. Allocate the physical RAM block
    try:
        shm = shared_memory.SharedMemory(name=SHM_NAME, create=True, size=FRAME_BYTES)
    except FileExistsError:
        shm = shared_memory.SharedMemory(name=SHM_NAME, create=False)

    cap = cv2.VideoCapture(0)
    # Force camera to match our exact memory allocation
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

            # Ensure strict frame size for memory byte alignment
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            detections = []

            try:
                results = model.predict(frame, imgsz=IMG_SIZE, conf=CONF_THRESH, device="cpu", verbose=False)
                r = results[0]

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

            except Exception as e:
                print("Inference failed:", e)
                annotated_frame = frame

            frame_id = (frame_id + 1) % 1_000_000
            
            curr_time = time.time()
            fps = 1 / max(curr_time - prev_time, 1e-5)
            prev_time = curr_time

            cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # 2. Safely push the JSON data to FastAPI using the IPC Manager
            with lock:
                shared_dict["latest_detections"] = {
                    "frame_id": frame_id,
                    "timestamp_ms": int(time.time() * 1000),
                    "detections": detections
                }
            
            # 3. Dump the raw Numpy bytes directly into the Shared Memory RAM block
            shm.buf[:FRAME_BYTES] = annotated_frame.tobytes()

    finally:
        # Prevent Zombie processes and memory leaks
        cap.release()
        shm.close()
        try:
            shm.unlink()
        except:
            pass

# ==========================================
# PROCESS 1: FASTAPI LIFECYCLE MANAGERS
# ==========================================
def start_vision():
    global vision_manager, shared_dict, frame_lock, vision_process, shm_read
    
    # Spin up the IPC (Inter-Process Communication) tools
    vision_manager = Manager()
    shared_dict = vision_manager.dict()
    shared_dict["latest_detections"] = None
    frame_lock = vision_manager.Lock()

    # Hunt down and destroy any ghost memory from a previous crash
    try:
        temp_shm = shared_memory.SharedMemory(name=SHM_NAME)
        temp_shm.close()
        temp_shm.unlink()
    except FileNotFoundError:
        pass

    # Launch YOLO on a new CPU core
    vision_process = Process(target=capture_loop, args=(shared_dict, frame_lock), daemon=True)
    vision_process.start()

    # Wait 2 seconds for YOLO to create the memory block, then connect FastAPI to it
    time.sleep(2)
    try:
        shm_read = shared_memory.SharedMemory(name=SHM_NAME, create=False)
    except Exception as e:
        print("Warning: Could not connect to Shared Memory on start:", e)

def stop_vision():
    global vision_process, shm_read, vision_manager
    print("🛑 Terminating YOLO process...")
    if vision_process and vision_process.is_alive():
        vision_process.terminate()
        vision_process.join()
    if shm_read:
        shm_read.close()
    if vision_manager:
        vision_manager.shutdown()

def get_current_frame():
    """Reads the raw bytes from RAM and reconstructs the image for FastAPI"""
    if not shm_read:
        return None
    frame_data = np.ndarray((FRAME_HEIGHT, FRAME_WIDTH, FRAME_CHANNELS), dtype=np.uint8, buffer=shm_read.buf)
    return frame_data.copy()

def get_snapshot_frame():
    return get_current_frame()

# ==========================================
# FASTAPI ROUTER & ENDPOINTS
# ==========================================
router = APIRouter(prefix="/vision", tags=["Vision"])

async def mjpeg_generator():
    while True:
        frame = get_current_frame()
        if frame is None:
            await asyncio.sleep(0.01)
            continue

        ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if not ret:
            await asyncio.sleep(0.01)
            continue
        
        jpg_bytes = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + jpg_bytes + b'\r\n')
        await asyncio.sleep(0.03)

@router.get("/video_feed")
async def video_feed(username: str = Depends(get_current_user_from_query)):
    return StreamingResponse(mjpeg_generator(), media_type='multipart/x-mixed-replace; boundary=frame')

@router.get("/latest", dependencies=[Depends(get_current_user)])
def get_latest():
    with frame_lock:
        detections_data = shared_dict.get("latest_detections")

    if detections_data is None:
        return {
            "detected": False,
            "fire_confidence": 0.0,
            "smoke_confidence": 0.0,
            "timestamp": None
        }

    detections = detections_data["detections"]
    timestamp = detections_data["timestamp_ms"]
    
    fire = [d for d in detections if d["class"].lower() == "fire"]
    smoke = [d for d in detections if d["class"].lower() == "smoke"]
    
    fire_conf = max([d["confidence"] for d in fire], default=0.0)
    smoke_conf = max([d["confidence"] for d in smoke], default=0.0)

    return {
        "detected": (fire_conf > 0 or smoke_conf > 0),
        "fire_confidence": fire_conf,
        "smoke_confidence": smoke_conf,
        "timestamp": timestamp
    }