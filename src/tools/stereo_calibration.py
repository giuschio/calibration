from math import degrees
import cv2 as cv
import matplotlib.pyplot as plt
import numpy as np
import re

from pathlib import Path
from os.path import join as pathjoin
from os.path import basename as basename

from scipy.spatial.transform import Rotation 



def natural_sort(l): 
  # from here https://stackoverflow.com/questions/4836710/is-there-a-built-in-function-for-string-natural-sort
  convert = lambda text: int(text) if text.isdigit() else text.lower()
  alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
  return sorted(l, key=alphanum_key)


def import_images(fpath: str) -> list:
  images = Path(fpath).glob("*.jpg")
  images_s = [str(p) for p in images]
  return natural_sort(images_s)


def stereo_calibrate(mtx_ir, dist_ir, mtx_rgb, dist_rgb, frames_ir, frames_rgb):
    #read the synched frames
    rgb_images_names = import_images(frames_rgb)
    ir_images_names = [pathjoin(frames_ir, basename(fpath)) for fpath in rgb_images_names]

    print(rgb_images_names)
    print(ir_images_names)

    ir_images = []
    rgb_images = []
    for im1, im2 in zip(ir_images_names, rgb_images_names):
        _im = cv.imread(im1, 1)
        ir_images.append(_im)
 
        _im = cv.imread(im2, 1)
        rgb_images.append(_im)
 
    #change this if stereo calibration not good.
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 100, 0.0001)
 
    rows = 7 #number of checkerboard rows.
    columns = 6 #number of checkerboard columns.
    world_scaling = 70 #change this to the real world square size. Or not.
 
    #coordinates of squares in the checkerboard world space
    objp = np.zeros((rows*columns,3), np.float32)
    objp[:,:2] = np.mgrid[0:rows,0:columns].T.reshape(-1,2)
    objp = world_scaling* objp


 
    #frame dimensions. Frames should be the same size.
    width = ir_images[0].shape[1]
    height = ir_images[0].shape[0]
 
    #Pixel coordinates of checkerboards
    imgpoints_left = [] # 2d points in image plane.
    imgpoints_right = []
 
    #coordinates of the checkerboard in checkerboard world space.
    objpoints = [] # 3d point in real world space
 
    for frame1, frame2 in zip(ir_images, rgb_images):
        gray1 = cv.cvtColor(frame1, cv.COLOR_BGR2GRAY)
        gray2 = cv.cvtColor(frame2, cv.COLOR_BGR2GRAY)
        c_ret1, corners1 = cv.findChessboardCorners(gray1, (rows, columns), None, cv.CALIB_CB_ADAPTIVE_THRESH | cv.CALIB_CB_FILTER_QUADS)
        c_ret2, corners2 = cv.findChessboardCorners(gray2, (rows, columns), None, cv.CALIB_CB_ADAPTIVE_THRESH | cv.CALIB_CB_FILTER_QUADS)
 
        if c_ret1 == True and c_ret2 == True:
            corners1 = cv.cornerSubPix(gray1, corners1, (11, 11), (-1, -1), criteria)
            corners2 = cv.cornerSubPix(gray2, corners2, (11, 11), (-1, -1), criteria)
 
            # cv.drawChessboardCorners(frame1, (5,8), corners1, c_ret1)
            # cv.imshow('img', frame1)
 
            # cv.drawChessboardCorners(frame2, (5,8), corners2, c_ret2)
            # cv.imshow('img2', frame2)
            # k = cv.waitKey(500)
 
            objpoints.append(objp)
            imgpoints_left.append(corners1)
            imgpoints_right.append(corners2)
            
 
    stereocalibration_flags = cv.CALIB_FIX_INTRINSIC
    ret, CM1, dist_ir, CM2, dist_rgb, R, T, E, F = cv.stereoCalibrate(objpoints, imgpoints_left, imgpoints_right, mtx_ir, dist_ir,
                                                                 mtx_rgb, dist_rgb, (width, height), criteria = criteria, flags = stereocalibration_flags)

    rotation = Rotation.from_dcm(R)
    
 
    print(ret)
    print(R)
    print("as rotation vector", rotation.as_rotvec() * 180/3.1415926)
    print("as euler angles (degs)", rotation.as_euler('xyz', degrees=True))
    print(T)
    return R, T
 
 
if __name__ == '__main__':
    mtx_ir = np.array([[504.7881, 0., 510.531], [0., 504.48370031854552, 508.3084765],[0., 0., 1.]])
    mtx_rgb = np.array([[619.612, 0., 640.98228], [0., 618.8887, 367.623],[0., 0., 1.]])
    dist_ir = np.array([-0.3052135 ,  0.08579099,  0.00048534, -0.00095727, 0., .0, .0, 0.])