# AI Surveillance System Powered By ESP32 and Pi 5 For FYP

This project is made in accordance to the completion of my computer science degree at Shah Abdul Latif University, Khairpur. This project is based on the YOLOv8 model combined with sensors like AMG8833, Flame IR Sensor and MQ-135 for the detection of threats, Smoke, Fire and Weapons. Furthermore, This project will be optimized to run on a Raspberry Pi 5 to serve as personal surveillance system.

## Features:
1. **Edge AI & Computer Vision (```vision.py```)**
    * **NCNN-Optimized Object Detection:** Utilizes a quantized YOLOv8 model running via the NCNN framework, specifically tuned for high-speed edge inference on ARM-based hardware (like the Raspberry Pi).
    * **Multi-Class Threat Extraction:** Independently identifies, tracks, and scores confidence levels for both "Fire" and "Smoke" classes simultaneously.
    * **Asynchronous Video Processing:** Employs a dedicated background capture thread (```capture_loop```) isolated with ```threading.Lock()``` to ensure heavy AI inference does not bottleneck the web server or drop camera frames.
    * **Live MJPEG Streaming:** Converts annotated OpenCV frames into a low-latency MJPEG byte stream, allowing real-time video monitoring in the browser.
2. **Continuous Multi-Sensor Data Fusion (```alert_engine.py```)**
    * **Mathematical Risk Scoring (Weighted Fusion):** Replaces brittle boolean thresholds (if/else) with a normalized equation. Sensors (Vision, Thermal, Flame, MQ135) are scored from ```0.0``` to ```1.0```, multiplied by tuned architectural weights, and combined into a fluid Risk Score.
    * **Thermal Rate of Rise (RoR) Calculus:** Tracks spatial and temporal temperature changes ($\frac{dT}{dt}$). It calculates the derivative of the thermal grid to detect dangerous temperature spikes (e.g., >2.0°C per second), preventing reliance solely on absolute temperature limits.
    * **Intelligent Noise Flooring:** Uses configuration constants (```VISION_FIRE_CONF```, etc.) as hard noise floors to mathematically zero-out sensor drift and low-confidence visual artifacts before they enter the fusion engine.
3. **State-Driven Alert Lifecycle (```alert_loop.py``` & ```alert_state.py```)**
    * **Alert State Machine:** Transitions threats through a strict lifecycle: ```NEW``` -> ```ACTIVE``` -> ```RESOLVED```.
    * **Persistence Windowing:** Requires a threat to maintain a high fusion score for a continuous duration (```PERSISTENCE_SECONDS```) before promoting it to ```ACTIVE```, mathematically eliminating transient false positives (like a passing lighter).
    * **Dynamic Severity Scaling:** Automatically categorizes incidents into ```LOW```, ```MEDIUM```, or ```HIGH``` severity bands based directly on the fused mathematical risk score.
    * **Asynchronous Evaluation Loop:** Runs the fusion engine continuously in the background via FastAPI's ```lifespan``` context manager, completely decoupled from frontend API requests.
4. **Evidence Capture & Data Persistence (alert_store.py)**
    * **Zero-Latency Evidence Snapshots:** Reaches into the active OpenCV frame buffer the exact millisecond a high-risk event triggers, saving a high-fidelity JPEG to the local filesystem without interrupting the live stream.
    * **SQLite Event Upserting:** Uses ```ON CONFLICT (id) DO UPDATE``` to efficiently mutate live alerts in the database (updating severity, confidence, and timestamps) without creating duplicate records.
    * **Automated CSV Incident Export:** Dynamically queries the SQLite history and generates a downloadable CSV report in memory (```io.StringIO```) for enterprise audit logging.
5. **Enterprise Security & Authentication (```login.py```)**
    * **OAuth2 / JWT Architecture:** Secures all system endpoints using JSON Web Tokens (JWT) with configurable expiration windows.
    * **Cryptographic Password Hashing:** Secures admin credentials using ```bcrypt``` salting and hashing, ensuring plaintext passwords never touch the database.
    * **Query-Parameter Media Authorization:** Protects static media assets (live video feeds and saved snapshot JPEGs) by parsing and validating JWTs directly from URL query parameters.
6. **Real-Time React Dashboard (```App.jsx```)**
    * **Dynamic Thermal Rendering:** Parses 64-point floating array data and renders an interpolated, color-mapped 8x8 heat grid with fixed ambient-to-fire temperature scales.
    * **Data Freshness Tracking:** Implements continuous heartbeat indicators that track the exact age (in milliseconds) of incoming sensor and vision payloads, changing color if telemetry lags.
    * **Secure Evidence Viewer:** Integrates a clickable UI element within the incident history log that fetches and renders authorized JPEG snapshots in a new browser tab.
    * **Responsive "Dark Mode" UI:** Built with Tailwind CSS, utilizing a grid-based layout that prioritizes high-contrast threat visibility (pulsing borders, conditional typography colors).

## File Structure:
```/Models```: houses all the trained models (both pytorch versions and the ONNX versions).

### sensors directory:
```AMG_MQ_IR```: the microcode thats flashed onto esp32.
```Sensor Fusion Wiring.txt```: txt file that goes over how all the sensors are wired up to the esp32.

### Backend Directory:
```bridge.py```:  code used to parse the csv data from the sensor fusion into a json for FastAPI.
```api.py```: used to convert the parsed json into an api endpoint.

### For the frontend:
to have a functional frontend, use this command to build all the dependencies.
```
npm create vite@latest fire-dashboard -- --template react
cd fire-dashboard
npm install

npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p

npm run dev
```

## To-do List:
- [x] Collect Datasets.
- [x] Train the model using the collected dataset.
- [x] Combine the sensors to send data properly as a CSV.
- [x] Turn that CSV into a JSON format and then Stream it as an API.
- [x] Stream the camera input through an API.
- [x] Add in alerts API.
- [x] Combine the camera and sensor data as a proper backend.
- [x] Add in a proper database for alerts and data storage.
- [x] Create a front end to show all the sensor data and camera input in a single clean dashboard.
- [x] Have the frontend show visuals from the camera and the thermal sensor.
- [x] Fix the vision detection issue where the detections don't appear on the frontend.
- [x] Fix the where the history doesn't appear on the frontend.
- [x] Add Authentication to the project
- [ ] Dockerize the whole project.
- [ ] Optimize and host the project onto a Raspberry pi 5.

## Directory Structure:
```
├── .devcontainer
│   └── devcontainer.json
├── ai_module
├── backend
│   ├── api
│   │   ├── alerts.py
│   │   ├── sensors.py
│   │   └── vision.py
│   ├── bridge
│   │   └── serial_bridge.py
│   ├── modules
│   │   ├── alert_config.py
│   │   ├── alert_loop.py
│   │   ├── alert_state.py
│   │   └── alerts_engine.py
│   ├── app.py
│   └── dummy_data.py
├── models
│   ├── trained_yolov8n_ncnn_model
│   │   ├── metadata.yaml
│   │   ├── model.ncnn.bin
│   │   ├── model.ncnn.param
│   │   └── model_ncnn.py
│   ├── trained_yolov8n_openvino_model
│   │   ├── metadata.yaml
│   │   ├── trained_yolov8n.bin
│   │   └── trained_yolov8n.xml
│   ├── trained_yolov8n.onnx
│   ├── trained_yolov8n.pt
│   ├── trained_yolov8s.onnx
│   └── trained_yolov8s.pt
├── sensors
│   ├── AMG_MQ_IR
│   │   └── AMG_MQ_IR.ino
│   └── Sensor Fusion Wiring.txt
├── .gitignore
├── README.md
├── main.py
└── requirements.txt
```