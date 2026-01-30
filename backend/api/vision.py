import cv2
from ultralytics import YOLO
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import threading
import time
import asyncio

# Load NCNN model
model = YOLO("models/trained_yolov8n_ncnn_model", task="detect")  # NCNN model folder
IMG_SIZE = 256
CONF_THRESH = 0.25

# Global Variables
latest_detections = None
frame_id = 0
detections_lock = threading.Lock()

# Webcam + shared frame
cap = None
frame_lock = threading.Lock()
output_frame = None

# Threaded capture + inference and output then as a proper Json
def capture_loop():
    global output_frame, cap, latest_detections, frame_id

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")

    prev_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        detections = []

        try:
            results = model.predict(
                frame,
                imgsz=IMG_SIZE,
                conf=CONF_THRESH,
                device="cpu"
            )

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

        with detections_lock:
            latest_detections = {
                "frame_id": frame_id,
                "timestamp_ms": int(time.time() * 1000),
                "detections": detections
            }

        curr_time = time.time()
        fps = 1 / max(curr_time - prev_time, 1e-5)
        prev_time = curr_time

        cv2.putText(
            annotated_frame,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        with frame_lock:
            output_frame = annotated_frame.copy()

# Start capture thread
threading.Thread(target=capture_loop, daemon=True).start()

# MJPEG generator for FastAPI
async def mjpeg_generator():
    global output_frame
    while True:
        with frame_lock:
            if output_frame is None:
                await asyncio.sleep(0.01)
                continue
            frame = output_frame.copy()

        # Encode as JPEG
        ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if not ret:
            await asyncio.sleep(0.01)
            continue
        jpg_bytes = buffer.tobytes()

        # Yield MJPEG frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg_bytes + b'\r\n')

        # Throttle ~30 FPS
        await asyncio.sleep(0.03)

# FastAPI app
router = APIRouter(prefix="/vision", tags=["Vision"])

@router.get("/video_feed")
async def video_feed():
    return StreamingResponse(mjpeg_generator(),
                             media_type='multipart/x-mixed-replace; boundary=frame')

# Optional health endpoint
@router.get("/health")
async def health():
    return {"status": "ok", "fps": "check visually on /video_feed"}

# Expose detections via API
@router.get("/detections/latest")
def get_latest_detections():
    with detections_lock:
        if latest_detections is None:
            return {"status": "no_detections"}
        return latest_detections
