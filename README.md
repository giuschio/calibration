## Camera calibration library using structure from motion


### Calibration of a monocular camera
script:    
`src/tools/camera_calibration.py`    
commandline usage:    
```bash
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