# AI Surveillance System Powered By ESP32 and Pi 5 For FYP

This project is made in accordance to the completion of my computer science degree at Shah Abdul Latif University, Khairpur. This project is based on the YOLOv8 model combined with sensors like AMG8833, Flame IR Sensor and MQ-135 for the detection of threats, Smoke, Fire and Weapons. Furthermore, This project will be optimized to run on a Raspberry Pi 5 to serve as personal surveillance system.

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
- [ ] Combine the camera and sensor data as a proper backend.
- [ ] Add in a proper database for alerts and data storage.
- [ ] Add Authentication to the project
- [ ] Create a front end to show all the sensor data and camera input in a single clean dashboard.
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