"""
Example: calibration of a kinect camera
- calibration of intrinsics of IR and RGB cameras
- estimation of stereo transformation between IR and RGB cameras
- exporting results to YAML
"""

from os.path import join as pathjoin
from os.path import basename

from tools.stereo_checkerboard_calibration import StereoRig, CheckerboardPattern

from tools.utils import import_images
from tools.camera_calibration import Camera

def main(rgb_dir, ir_dir, stereo_rgb_dir=None, stereo_ir_dir=None, fname="camera_info.yaml"):
    rgb_calibrator = Camera(camera_model="OPENCV")
    rgb_calibrator.calibrate(image_dir=rgb_dir)

    ir_calibrator = Camera(camera_model="OPENCV")
    ir_calibrator.calibrate(image_dir=ir_dir)

    if stereo_ir_dir is None or stereo_rgb_dir is None:
        stereo_rgb_dir, stereo_ir_dir = rgb_dir, ir_dir
    #read the synched frames
    rgb_stereo_images = import_images(stereo_rgb_dir)
    ir_stereo_images = [pathjoin(stereo_ir_dir, basename(fpath)) for fpath in rgb_stereo_images]
    stereo_rig = StereoRig()
    stereo_rig.k1 = ir_calibrator.k
    stereo_rig.d1 = ir_calibrator.d
    stereo_rig.k2 = rgb_calibrator.k
    stereo_rig.d2 = rgb_calibrator.d
    pattern = CheckerboardPattern(rows = 7, columns = 6, square_size = 70)
    stereo_rig.calibrate(frames1=ir_stereo_images, frames2=rgb_stereo_images, pattern=pattern)
    stereo_rig.export_yaml(fname, cam1_name="depth", cam2_name="rgb")


if __name__ == "__main__":
    proot = "/home/harmony_asl/pyhon_workspace/0_DATA/calibration/images"
    main(rgb_dir=pathjoin(proot, "rgb_calibration"), 
         ir_dir=pathjoin(proot, "ir_calibration"), 
         stereo_rgb_dir=pathjoin(proot, "stereo_calibration/img_rgb"), 
         stereo_ir_dir=pathjoin(proot, "stereo_calibration/img_ir"))