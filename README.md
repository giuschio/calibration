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


### Camera-to-camera calibration with checkerboard pattern (using OPENCV)
Estimate the rotation and translation between two calibrated cameras.   
A checkerboard pattern can be generated using [https://calib.io/pages/camera-calibration-pattern-generator](https://calib.io/pages/camera-calibration-pattern-generator).   
script:    
`src/tools/stereo_checkerboard_calibration.py`    
commandline usage:    
```bash
source venv/bin/activate
# basic usage (prints results to terminal)
python3 src/tools/stereo_checkerboard_calibration.py abs/path/to/cam_1/images abs/path/to/cam_2/images abs/path/to/cam_1/info.txt abs/path/to/cam_2/info.txt --checkerboard ROWSxCOLUMNSxSQUARE_SIZE
# export intrinsics of both cameras and cam-to-cam extrinsics to yaml file
python3 src/tools/stereo_checkerboard_calibration.py abs/path/to/cam_1/images abs/path/to/cam_2/images abs/path/to/cam_1/info.txt abs/path/to/cam_2/info.txt --checkerboard ROWSxCOLUMNSxSQUARE_SIZE --savepath abs/path/to/stereo_camera_info.yaml
```
as module:
```python
from tools.stereo_checkerboard_calibration import StereoRig, CheckerboardPattern
from tools.utils import import_images
stereo = StereoRig()
# assign camera intrinsics (assumes cam1 and cam2 are calibrated)
# k1, k2 are np.ndarray[3,3]
# d1, d2 are np.ndarray[4]
stereo.k1, stereo.d1 = ...
stereo.k2, stereo.d2 = ...
# define checkerboard
pattern = CheckerboardPattern(rows, columns, square_size)
frames1 = import_images('abs/path/to/cam_1/images')
frames2 = import_images('abs/path/to/cam_2/images')
# the calibration function assumes that frames1 and frames2 are synchronized (i.e. the i-th image in frames1 must correspond to the i-th image in frames2)
stereo.calibrate_with_checkerboard(frames1, frames2, pattern)
# export intrinsics of both cameras and cam-to-cam extrinsics to yaml file
stereo.export_yaml(fpath='abs/path/to/stereo_into.yaml')
```