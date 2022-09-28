## Camera calibration library using structure from motion

### Installation
Clone this repository, create a virtual environment and install requirements:
```bash
git clone git@github.com:giuschio/calibration.git camera_calibration
cd camera_calibration
mkdir venv
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```


### Calibration of a monocular camera
script:    
`src/tools/camera_calibration.py`    
commandline usage:    
```bash
source venv/bin/activate
# basic usage (prints camera info to terminal)
python3 src/tools/camera_calibration.py abs/path/to/images OPENCV
# export camera_info to file
python3 src/tools/camera_calibration.py abs/path/to/images OPENCV --savepath abs/path/to/camera_info.txt
```
as module:
```python
from tools.camera_calibration import Camera
cam = Camera(camera_model="OPENCV")
# basic usage (prints camera info to terminal)
cam.calibrate(input_dir="abs/path/to/images")
# export camera_info to file
cam.calibrate(input_dir="abs/path/to/images", savepath='abs/path/to/camera_info.txt')
```