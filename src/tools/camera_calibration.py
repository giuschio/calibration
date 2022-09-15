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
"""

import numpy as np
import os
import pathlib
import pycolmap
import shutil


class CameraCalibrator:
    supported_models = ["OPENCV", "FULL_OPENCV"]

    def __init__(self, camera_model="OPENCV") -> None:
        # this code supports the OPENCV (also known as radtan, plum_bob) and FULL_OPENCV
        # see https://colmap.github.io/cameras.html for available camera models
        if camera_model not in CameraCalibrator.supported_models:
            raise ValueError("Invalid camera model. This code only supports the following models:\n " +
                              str(CameraCalibrator.supported_models) + "\n" + 
                              "see https://colmap.github.io/cameras.html for more details")

        self.camera_model = camera_model
        # (fx, fy, cx, cy, k1, k2, p1, p2, ...kn)
        self.camera_info = None
        
    def __call__(self, image_dir=None, output_path=None, verbose=True) -> None:
        image_dir = pathlib.Path(os.getcwd()) / "images" if image_dir is None else pathlib.Path(image_dir)
        # create _tmp directory to store COLMAP artifacts
        _tmp_dir = os.getcwd() if output_path is None else output_path
        _tmp_dir = pathlib.Path(_tmp_dir) / "_tmp"
        _tmp_dir.mkdir(parents=True, exist_ok=True)
        database_path = _tmp_dir / "database.db"
        print("removing old datatabase (if any)...")
        if os.path.exists(database_path): 
            os.remove(database_path)

        # pipeline is defined here: https://github.com/colmap/pycolmap/tree/master/pipeline
        pycolmap.extract_features(database_path=database_path, 
                                  image_path=image_dir,
                                  camera_mode=pycolmap.CameraMode.SINGLE,
                                  camera_model=self.camera_model,
                                  verbose=verbose)
        pycolmap.match_exhaustive(database_path, verbose=verbose)

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
        # save camera info if a path was provided
        if output_path is not None:
            output_path = pathlib.Path(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            np.savetxt(str(output_path / "camera_params.txt"), self.camera_info, delimiter=',') 
        print("camera model:", self.camera_model)
        print("camera parameters (fx, fy, cx, cy, k1, k2, p1, p2, ...kn)")
        print(np.array2string(self.camera_info, separator=', '))

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
    calib = CameraCalibrator()
    calib()
    print(calib.k)
    print(calib.d)
    