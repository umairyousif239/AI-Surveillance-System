from serial import Serial
import requests
import time

SERIAL_PORT = "/dev/ttyUSB0"   # or COM3 on Windows
BAUDRATE = 115200
API_URL = "http://127.0.0.1:8000/sensor-frame"

ser = Serial(SERIAL_PORT, BAUDRATE, timeout=1)
time.sleep(1)

while True:
    line = ser.readline().decode("utf-8", errors="ignore").strip()
    if not line or not line.startswith("F,"):
        continue
    try:
        parts = line.split(",")
        
        payload = {
            "frame_id": int(parts[1]),
            "timestamp_ms": int(parts[2]),
            "flame": int(parts[3]),
            "mq135_raw": int(parts[4]),
            "thermal": [float(x) for x in parts[5:]]
        }
        response = requests.post(API_URL, json=payload, timeout=0.2)
        print("POST", response.status_code)
    except Exception as e:
        print("Parse error:", e)
