# AI Survellance System Powered By ESP32 and Pi 5 For FYP

This project in accordance to the completion of my computer science degree at Shah Abdul Latif University, Khairpur. This project is based on the YOLOv8 model combined with sensors like AMG8833, Flame IR Sensor and MQ-135 for the detection of threats, Smoke, Fire and Weapons. Furthermore, This project will be optimized to run on a Raspberry Pi 5 to serve as personal surveillance system.

## File Structure:
```/Models```: houses all the trained models (both pytorch versions and the ONNX versions).

### sensors directory:
```AMG_MQ_IR```: the microcode thats flashed onto esp32.
```Sensor Fusion Wiring.txt```: txt file that goes over how all the sensors are wired up to the esp32.

### Backend Directory:
```bridge.py```:  code used to parse the csv data from the sensor fusion into a json for FastAPI.
```api.py```: used to convert the parsed json into an api endpoint.

## Todo List:
- [x] Collect Datasets.
- [x] Train the model using the collected dataset.
- [x] Combine the sensors to send data properly as a CSV.
- [x] Turn that CSV into a JSON format and then Stream it as an API.
- [x] Stream the camera input through an API.
- [ ] Add in alerts API.
- [ ] Add Authentication to the project
- [ ] combine the camera and sensor data as a proper backend.
- [ ] Create a front end to show all the sensor data and camera input in a single clean dashboard.
- [ ] Dockerize the whole project.
- [ ] Optimize and host the project onto a Raspberry pi 5.