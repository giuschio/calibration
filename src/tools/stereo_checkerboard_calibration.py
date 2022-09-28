import argparse
import cv2 as cv
import numpy as np
import typing

from os.path import basename as basename

from camera_calibration import Camera
from utils import dict_to_yaml, import_images


class CheckerboardPattern:
    def __init__(self, rows, columns, square_size) -> None:
        self.rows = rows
        self.columns = columns
        self.square_size = square_size


class StereoRig:
    def __init__(self) -> None:
        self.k1 = None
        self.d1 = None
        self.k2 = None
        self.d2 = None

        self.R_1to2 = None
        self.T_1to2 = None

    def export_yaml(self, fpath, cam1_name:str = "cam1", cam2_name:str = "cam2") -> None:
        res = dict()
        res[cam1_name+"_k"] = np.array([self.k1[0, 0], self.k1[1, 1], self.k1[0, 2], self.k1[1, 2] ]).tolist()
        res[cam1_name+"_d"] = self.d1.tolist()
        res[cam2_name+"_k"] = np.array([self.k2[0, 0], self.k2[1, 1], self.k2[0, 2], self.k2[1, 2] ]).tolist()
        res[cam2_name+"_d"] = self.d2.tolist()

        res[cam1_name+"_to_"+cam2_name+"_rotation"] = self.R_1to2.flatten().tolist()
        res[cam1_name+"_to_"+cam2_name+"_translation"] = self.T_1to2.flatten().tolist()

        dict_to_yaml(data=res, fpath=fpath)
        print("\nSaved camera parameters to " + fpath)

    def calibrate_with_checkerboard(self, frames1: typing.List[str], frames2: typing.List[str], pattern: CheckerboardPattern, view_corners=False):
        """
        The code is this function is derived from https://github.com/TemugeB/python_stereo_camera_calibrate.
        License of the original code (from https://github.com/TemugeB/python_stereo_camera_calibrate)

        Copyright [yyyy] [name of copyright owner]

        Licensed under the Apache License, Version 2.0 (the "License");
        you may not use this file except in compliance with the License.
        You may obtain a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

        Unless required by applicable law or agreed to in writing, software
        distributed under the License is distributed on an "AS IS" BASIS,
        WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
        See the License for the specific language governing permissions and
        limitations under the License.
        """
        imgs1 = list()
        imgs2 = list()
        for im1, im2 in zip(frames1, frames2):
            _im = cv.imread(im1, 1)
            imgs1.append(_im)
    
            _im = cv.imread(im2, 1)
            imgs2.append(_im)

        #change this if stereo calibration not good.
        criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 100, 0.0001)

        #coordinates of squares in the checkerboard world space
        objp = np.zeros((pattern.rows*pattern.columns,3), np.float32)
        objp[:,:2] = np.mgrid[0:pattern.rows,0:pattern.columns].T.reshape(-1,2)
        objp = pattern.square_size* objp

        #frame dimensions. Frames should be the same size.
        width = imgs1[0].shape[1]
        height = imgs2[0].shape[0]
    
        #Pixel coordinates of checkerboards
        imgpoints_1 = [] # 2d points in image plane.
        imgpoints_2 = []
    
        #coordinates of the checkerboard in checkerboard world space.
        objpoints = [] # 3d point in real world space
    
        for frame1, frame2 in zip(imgs1, imgs2):
            gray1 = cv.cvtColor(frame1, cv.COLOR_BGR2GRAY)
            gray2 = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)
            c_ret1, corners1 = cv.findChessboardCorners(gray1, (pattern.rows, pattern.columns), None, cv.CALIB_CB_ADAPTIVE_THRESH | cv.CALIB_CB_FILTER_QUADS)
            c_ret2, corners2 = cv.findChessboardCorners(gray2, (pattern.rows, pattern.columns), None, cv.CALIB_CB_ADAPTIVE_THRESH | cv.CALIB_CB_FILTER_QUADS)
    
            if c_ret1 == True and c_ret2 == True:
                corners1 = cv.cornerSubPix(gray1, corners1, (11, 11), (-1, -1), criteria)
                corners2 = cv.cornerSubPix(gray2, corners2, (11, 11), (-1, -1), criteria)
                if view_corners:
                    cv.drawChessboardCorners(frame1, (5,8), corners1, c_ret1)
                    cv.imshow('img', frame1)
        
                    cv.drawChessboardCorners(frame2, (5,8), corners2, c_ret2)
                    cv.imshow('img2', frame2)
                    key = cv.waitKey(500)
    
                objpoints.append(objp)
                imgpoints_1.append(corners1)
                imgpoints_2.append(corners2)

        stereocalibration_flags = cv.CALIB_FIX_INTRINSIC
        # see here https://docs.opencv.org/3.4/d9/d0c/group__calib3d.html#ga91018d80e2a93ade37539f01e6f07de5
        success, CM1, dist_ir, CM2, dist_rgb, R, T, E, F = cv.stereoCalibrate(objpoints, 
                                                                          imgpoints_1, 
                                                                          imgpoints_2, 
                                                                          self.k1, 
                                                                          self.d1,
                                                                          self.k2, 
                                                                          self.d2, 
                                                                          (width, height), 
                                                                          criteria = criteria, 
                                                                          flags = stereocalibration_flags)

        self.R_1to2 = np.array(R)
        self.T_1to2 = np.array(T)

        print("\n\n-------- RESULTS ----------")
        print("final reprojection error: ", success)
        print("rotation cam1 -> cam2 (as rotation matrix)")
        print( np.array2string(self.R_1to2, separator=", "))
        print("rotation cam1 -> cam2 (as xyz rotation vector)")
        print( np.array2string(np.transpose(cv.Rodrigues(self.R_1to2)[0]) * 180.0/np.pi, separator=" ,"))
        print("translation cam1 -> cam2")
        print(np.array2string(np.transpose(self.T_1to2), separator=", "))

        return success


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir_1", help="Absolute path to folder containing camera images (camera1).")
    parser.add_argument("input_dir_2", help="Absolute path to folder containing camera images (camera2).")
    parser.add_argument("camera_info_1", help="Absolute path to camera_info.txt file for camera1.")
    parser.add_argument("camera_info_2", help="Absolute path to camera_info.txt file for camera2.")
    parser.add_argument("--checkerboard", help="Checkerboard parameters ROWSxCOLUMNSxSQUARE_SIZE (e.g. 7x6x70).")
    parser.add_argument("--savepath", help="Absolute path where the results should be saved. Must be a .yaml file. If no path is provided, the camera info will be just printed in the terminal.")
    args = parser.parse_args()

    checkerboard_params = str(args.checkerboard) if args.checkerboard else None
    assert(checkerboard_params is not None and "calibration without checkerboard is not implemented yet")

    stereo_rig = StereoRig()
    cam1, cam2 = Camera(), Camera()
    cam1.camera_info = np.loadtxt(str(args.camera_info_1))
    cam2.camera_info = np.loadtxt(str(args.camera_info_2))
    stereo_rig.k1, stereo_rig.d1 = cam1.k, cam1.d
    stereo_rig.k2, stereo_rig.d2 = cam2.k, cam2.d

    rows, cols, size = checkerboard_params.split(sep="x")
    checkerboard = CheckerboardPattern(rows=int(rows), columns=int(cols), square_size=float(size))

    # get frames
    print("\n[WARN]: This script assumes that the frames in input_dir_1 and input_dir_2 are synchronized. " \
          "That is, the i-th image in input_dir_1 must correspond to the i-th image in input_dir_2.")
    answer = input("        Are the frames in input_dir_1 and input_dir_2 are synchronized? [y/n]  ") 
    while answer not in ["y", "n"]: answer = input("Please enter [y] or [n].  ")

    if bool(answer in ["y"]):
        print("\nEstimating camera-to-camera transformation....")
        frames1 = import_images(args.input_dir_1)
        frames2 = import_images(args.input_dir_2)

        stereo_rig.calibrate_with_checkerboard(frames1=frames1, frames2=frames2, pattern=checkerboard)
        if args.savepath: stereo_rig.export_yaml(fpath=args.savepath)
