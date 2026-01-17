```/Models```: houses all the trained models (both pytorch versions and the ONNX versions).

# sensors directory
```AMG_MQ_IR```: the microcode thats flashed onto esp32
```Sensor Fusion Wiring.txt```: txt file that goes over how all the sensors are wired up to the esp32.

# Backend Directory
```bridge.py```:  code used to parse the csv data from the sensor fusion into a json for FastAPI.
```api.py```: used to convert the parsed json into an api endpoint.