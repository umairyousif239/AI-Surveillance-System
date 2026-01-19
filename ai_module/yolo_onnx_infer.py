import cv2
from ultralytics import YOLO
import time

# ===============================
# 1️⃣ Load NCNN model via Ultralytics
# ===============================
model = YOLO("models/trained_yolov8n_ncnn_model")  # folder with .param + .bin
IMG_SIZE = 256
CONF_THRESH = 0.5
IOU_THRESH = 0.5
FRAME_SKIP = 1

# ===============================
# 2️⃣ Open webcam
# ===============================
cap = cv2.VideoCapture(0)
frame_count = 0

# ===============================
# 3️⃣ Main loop
# ===============================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % FRAME_SKIP != 0:
        cv2.imshow("YOLOv8n NCNN", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break
        continue

    # ===============================
    # CPU inference timing
    # ===============================
    start_cpu = time.time()
    _ = model.predict(frame, imgsz=IMG_SIZE, conf=CONF_THRESH, iou=IOU_THRESH, device="cpu")
    end_cpu = time.time()
    fps_cpu = 1 / (end_cpu - start_cpu)

    # ===============================
    # Vulkan GPU inference timing
    # ===============================
    start_gpu = time.time()
    results = model.predict(frame, imgsz=IMG_SIZE, conf=CONF_THRESH, iou=IOU_THRESH, device="vulkan:0")
    end_gpu = time.time()
    fps_gpu = 1 / (end_gpu - start_gpu)

    # ===============================
    # Annotate and display
    # ===============================
    annotated_frame = results[0].plot()
    cv2.putText(annotated_frame, f"FPS CPU: {fps_cpu:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(annotated_frame, f"FPS Vulkan: {fps_gpu:.1f}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow("YOLOv8n NCNN Vulkan Benchmark", annotated_frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
