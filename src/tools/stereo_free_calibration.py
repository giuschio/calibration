import argparse
import cv2 as cv
import numpy as np
import pycolmap
import typing

from os.path import basename as basename

from camera_calibration import Camera
from utils import dict_to_yaml, import_images


class StereoRig:
    def __init__(self) -> None:
        self.cam1 = None
        self.cam2 = None

        self.R_1to2 = None
        self.T_1to2 = None

    def calibrate(self, frames1: typing.List[str], frames2: typing.List[str], view_corners=True):
        imgs1 = list()
        imgs2 = list()
        # read images
        for im1, im2 in zip(frames1, frames2):
            _im = cv.imread(im1, 1)
            imgs1.append(cv.cvtColor(_im, cv.COLOR_BGR2GRAY))
    
            _im = cv.imread(im2, 1)
            imgs2.append(cv.cvtColor(_im, cv.COLOR_BGR2GRAY))

        # define colmap cameras
        cam1_model = 'OPENCV' if len(self.cam1.camera_info == 8) else 'FULL_OPENCV'
        camera1 = pycolmap.Camera(
            model=cam1_model,
            width=imgs1[0].shape[1],
            height=imgs1[0].shape[0],
            params=self.cam1.camera_info,
        )
        cam2_model = 'OPENCV' if len(self.cam2.camera_info == 8) else 'FULL_OPENCV'
        camera2 = pycolmap.Camera(
            model=cam2_model,
            width=imgs2[0].shape[1],
            height=imgs2[0].shape[0],
            params=self.cam2.camera_info,
        )

        # SIFT feature matching (OPENCV)
        all_keypoints_1 = list()
        all_keypoints_2 = list()
        sift = cv.SIFT_create()
        ratio_check = 0.7
        for frame1, frame2 in zip(imgs1, imgs2):
            keypoints_1, descriptors_1 = sift.detectAndCompute(frame1,None)
            keypoints_2, descriptors_2 = sift.detectAndCompute(frame2,None)
            # BFMatcher with default params
            bf = cv.BFMatcher()
            knn_matches = bf.knnMatch(descriptors_1, descriptors_2, k=2)
            matches = []
            for m, n in knn_matches:
                if m.distance < ratio_check * n.distance:
                    matches.append([m])

            if view_corners:
                img3 = cv.drawMatchesKnn(frame1,keypoints_1,frame2,keypoints_2,matches,None)
                cv.imshow('SIFT matches', img3)
                key = cv.waitKey(500)

            all_keypoints_1 += [keypoints_1[mat[0].queryIdx].pt for mat in matches] 
            all_keypoints_2 += [keypoints_2[mat[0].trainIdx].pt for mat in matches]

        # estimate two-view geometry
        answer = pycolmap.two_view_geometry_estimation(all_keypoints_1, all_keypoints_2, camera1, camera2)
        qvec, tvec = answer['qvec'], answer['tvec']
        cv.core.Quat(qvec)
        print("rotation")
        print(cv.Rodrigues(qvec))
        print("offset direction (normalized)")
        print(tvec/np.linalg.norm(tvec))


if __name__ == '__main__':
    
    stereo_rig = StereoRig()
    frames1 = import_images("/home/harmony_asl/pyhon_workspace/0_DATA/calibration/images/stereo_calibration/img_ir")
    frames2 = import_images("/home/harmony_asl/pyhon_workspace/0_DATA/calibration/images/stereo_calibration/img_rgb")

    cam1, cam2 = Camera(), Camera()
    cam1.camera_info = np.loadtxt('/home/harmony_asl/pyhon_workspace/0_DATA/calibration/images/ir_info_11.txt')
    cam2.camera_info = np.loadtxt('/home/harmony_asl/pyhon_workspace/0_DATA/calibration/images/rgb_info_11.txt')
    stereo_rig.cam1 = cam1
    stereo_rig.cam2 = cam2
    
    stereo_rig.calibrate(frames1, frames2, view_corners=False)
