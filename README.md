# AI Surveillance System Powered By ESP32 and Pi 5 For FYP

This project is made in accordance to the completion of my computer science degree at Shah Abdul Latif University, Khairpur. This project is based on the YOLOv8 model combined with sensors like AMG8833, Flame IR Sensor and MQ-135 for the detection of threats, Smoke, Fire and Weapons. Furthermore, This project will be optimized to run on a Raspberry Pi 5 to serve as personal surveillance system.

## Features:
### 1. Core Intelligence & Processing
* **Edge-Based AI Inference:** Utilizes a custom-trained YOLOv8 model optimized via the **NCNN framework** to detect fire and smoke locally on a Raspberry Pi 5 without cloud dependency.
* **Mathematical Fusion Engine:** A decoupled background loop that calculates a normalized **Risk Score** by cross-referencing AI vision data with physical sensor telemetry to reduce false positives.
* **Thermal Rate of Rise (RoR) Calculation:** Monitors how fast temperature spikes per second rather than waiting for an absolute heat threshold, allowing for faster ```Flash Fire``` detection.
* **State-Driven Alert Lifecycle Manager:** Transitions threats through strict **NEW**, **ACTIVE**, and **RESOLVED** phases using ```persistence windowing``` to verify hazards over time.
### 2. Hardware & Connectivity
* **Multi-Modal Sensor Array:** Integrates an **AMG8833** thermal camera, **MQ-135** gas/smoke sensor, and **Flame IR** sensor for secondary hardware validation of visual threats.
* **Hardwired Serial USB Bridge:** Connects the ESP32 sensor manager to the Raspberry Pi 5 via USB to eliminate wireless latency or interference during an emergency.
* **Standalone Wireless Access Point (WAP):** The system broadcasts its own encrypted ad-hoc network, ensuring it remains operational and accessible even if municipal internet infrastructure fails.
![System Architecture](./repo_resources/images/system_architecture_diagram.png)
### 3. Software & Security
* **Asynchronous Vision Pipeline:** Employs Python's multiprocessing and shared memory to isolate heavy AI math from the web server, maintaining a fluid 25 to 30 FPS camera feed.
* **Token-Based Authentication (JWT):** Secures all REST APIs, evidence snapshots, and live video streams using **JSON Web Tokens** and **bcrypt** password hashing.
* **Dual SQLite Database Architecture:** Uses separate, lightweight databases for secure user authentication (**auth.db**) and persistent, high-efficiency event logging (**alerts.db**).
* **Containerized Microservices:** The entire software stack is deployed via **Docker**, ensuring environment isolation and easy portability across different hardware.
### 4. User Interface & Monitoring
* **Real-Time React Web Dashboard:** A high-contrast dark-mode interface featuring dynamic thermal grid color-mapping, live MJPEG streaming, and interactive alert history.
* **Hybrid Android Mobile Application:** A Capacitor-powered application that provides mobile monitoring, remote push notifications, and evidence retrieval over the local network.
* **Low-Latency Evidence Capture:** Automatically captures high-fidelity visual snapshots with bounding box overlays the moment an alert becomes ```ACTIVE``` for later audit.
* **Client-Side CSV Export:** Allows administrators to generate and download structured incident reports directly from the browser for record-keeping.

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