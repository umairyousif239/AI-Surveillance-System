import cv2
from ultralytics import YOLO
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import threading
import time
import asyncio

# Load NCNN model
model = YOLO("models/trained_yolov8n_ncnn_model")  # NCNN model folder
IMG_SIZE = 256
CONF_THRESH = 0.25

# Webcam + shared frame
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Cannot open webcam")

frame_lock = threading.Lock()
output_frame = None

# Threaded capture + inference
def capture_loop():
    global output_frame
    prev_time = time.time()
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.01)
            continue

        # Run NCNN inference
        try:
            results = model.predict(frame, imgsz=IMG_SIZE, conf=CONF_THRESH, device="cpu")
            annotated_frame = results[0].plot()
        except Exception as e:
            print("Inference failed:", e)
            annotated_frame = frame

        # Add FPS overlay
        curr_time = time.time()
        fps = 1 / max(curr_time - prev_time, 1e-5)
        prev_time = curr_time
        cv2.putText(annotated_frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Save frame thread-safely
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
app = FastAPI()

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(mjpeg_generator(),
                             media_type='multipart/x-mixed-replace; boundary=frame')

# Optional health endpoint
@app.get("/health")
async def health():
    return {"status": "ok", "fps": "check visually on /video_feed"}

# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
