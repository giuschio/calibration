"""
Created by Giulio Schiavi (15 Sept 2022)
       _
    ___|
   [n n]
 o=     =o
   |GS_|
    d b

pycolmap documentation
https://github.com/colmap/pycolmap

Get intrinsics and distortion parameters of a monocular camera. 
"""
import argparse
import numpy as np
import os
import pathlib
import pycolmap
import shutil


class Camera:
    supported_models = ["OPENCV", "FULL_OPENCV"]

    def __init__(self, camera_model="OPENCV") -> None:
        # this code supports the OPENCV (also known as radtan, plum_bob) and FULL_OPENCV
        # see https://colmap.github.io/cameras.html for available camera models
        if camera_model not in Camera.supported_models:
            raise ValueError("Invalid camera model. This code only supports the following models:\n " +
                              str(Camera.supported_models) + "\n" + 
                              "see https://colmap.github.io/cameras.html for more details")

        self.camera_model = camera_model
        # (fx, fy, cx, cy, k1, k2, p1, p2, ...kn)
        self.camera_info = None

    def export_txt(self, savepath):
        # make sure the output directory exists
        pathlib.Path(os.path.dirname(savepath)).mkdir(parents=True, exist_ok=True)
        print("\nSaved camera parameters to " + savepath)
        np.savetxt(savepath, self.camera_info, delimiter=',', header='camera parameters (fx, fy, cx, cy, k1, k2, p1, p2, ...kn)') 
        
    def calibrate(self, image_dir=None, working_dir=None, savepath=None) -> None:
        image_dir = pathlib.Path(os.getcwd()) / "images" if image_dir is None else pathlib.Path(image_dir)
        # create _tmp directory to store COLMAP artifacts
        _tmp_dir = os.getcwd() if working_dir is None else working_dir
        _tmp_dir = pathlib.Path(_tmp_dir) / "_tmp_calibration"
        _tmp_dir.mkdir(parents=True, exist_ok=True)
        database_path = _tmp_dir / "database.db"
        print("removing old datatabase (if any)...")
        if os.path.exists(database_path): 
            os.remove(database_path)

        # pipeline is defined here: https://github.com/colmap/pycolmap/tree/master/pipeline
        pycolmap.extract_features(database_path=database_path, 
                                  image_path=image_dir,
                                  camera_mode=pycolmap.CameraMode.SINGLE,
                                  camera_model=self.camera_model)
        pycolmap.match_exhaustive(database_path)

        # options are defined here: https://github.com/colmap/pycolmap/blob/master/pipeline/sfm.cc
        options = dict(ba_refine_focal_length=True,
                       ba_refine_principal_point=True,
                       ba_refine_extra_params=True)
        # options = pycolmap.IncrementalMapperOptions(**options)
        maps = pycolmap.incremental_mapping(database_path=database_path, 
                                            image_path=image_dir, 
                                            output_path=_tmp_dir,
                                            options=options)
        # reconstruction and camera class bindings are defined here: https://github.com/colmap/pycolmap/tree/master/reconstruction
        self.camera_info = np.array(maps[0].cameras[1].params)
        print("\n\n-------- RESULTS ----------")
        print("camera model:", self.camera_model)
        print("camera parameters (fx, fy, cx, cy, k1, k2, p1, p2, ...kn)")
        print(np.array2string(self.camera_info, separator=', '))

        # save camera info if a path was provided
        if savepath is not None: self.export_txt(savepath)

        # remove temporary files
        shutil.rmtree(_tmp_dir)

    def check_calibrated(self):
        if self.camera_info is None:
            raise ValueError("camera_info is None, did you calibrate the camera?")
    
    @property
    def k(self):
        self.check_calibrated()
        k = np.identity(3)
        k[0, 0] = self.camera_info[0]
        k[1, 1] = self.camera_info[1]
        k[0, 2] = self.camera_info[2]
        k[1, 2] = self.camera_info[3]
        return k

    @property
    def d(self):
        self.check_calibrated()
        return np.array(self.camera_info[4:])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", help="Absolute path to images")
    parser.add_argument("camera_model", help="Distortion model. Either OPENCV or FULL_OPENCV. See COLMAP documentation for more details: https://colmap.github.io/cameras.html")
    parser.add_argument("--working_dir", help="Absolute path to working directory. Used to store colmap workspace in _tmp_calibration. If no path is provided, the current directory will be used.")
    parser.add_argument("--savepath", help="Absolute path where the results should be saved. Must be a .txt file. If no path is provided, the camera info will be just printed in the terminal.")
    args = parser.parse_args()

    input_dir = str(args.input_dir)
    camera_model = str(args.camera_model)
    working_dir = str(args.working_dir) if args.working_dir else None
    savepath = str(args.savepath) if args.savepath else None

    camera = Camera(camera_model=camera_model)
    camera.calibrate(image_dir=input_dir, working_dir=working_dir, savepath=savepath)
