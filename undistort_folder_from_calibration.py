import cv2
import timeit
import os
import datetime
import sys
import argparse
import numpy as np
import glob
from calibrate_camera import calibration_img_width_file, calibration_img_height_file, calibration_mtx_file, calibration_dist_file
from undistort_folder import store_or_show_undistorted_images

parser = argparse.ArgumentParser()
parser.add_argument("calibrationdir", help="Directory containing parameters to perform undistortion")
parser.add_argument("inputdir", help="Directory containing images to be undistorted")
parser.add_argument("-o", "--outputdir", default=None, dest="outputdir", help="(Optional) Directory to store undistorted images in (if not supplied images are only displayed)")
parser.add_argument("-t", "--timeout", default=0, type=int, dest="timeout", help="(Optional) Timeout for images to be shown (negative to show nothing)")

# read calibrationdir and extract calibration parameter:
#   calibration_img_width   =>  width of the images
#   calibration_img_height  =>  heith of the images
#   calibration_mtx         =>  3x3 floating-point camera intrinsic matrix 
#   calibration_dist        =>  vector of distortion coefficients
def load_calibration_parameters(calibrationdir):
    # compose path to files
    calibration_img_width_file = os.path.join(calibrationdir, calibration_img_width_file)
    calibration_img_height_file = os.path.join(calibrationdir, calibration_img_height_file)
    calibration_mtx_file = os.path.join(calibrationdir, calibration_mtx_file)
    calibration_dist_file = os.path.join(calibrationdir, calibration_dist_file)
    # load data
    calibration_img_width = np.load(calibration_img_width_file)
    calibration_img_height = np.load(calibration_img_height_file)
    calibration_mtx = np.load(calibration_mtx_file)
    calibration_dist = np.load(calibration_dist_file)
    # return parameters
    return calibration_img_width, calibration_img_height, calibration_mtx, calibration_dist

# parse arguments
def parse():
    args = parser.parse_args()
    if not os.path.exists(args.calibrationdir):
        print(F"ERROR: noexistent calibration directory '{args.calibrationdir}'", file=sys.stderr)
        exit(1)
    if not os.path.exists(args.inputdir):
        print(F"ERROR: noexistent source directory '{args.inputdir}'", file=sys.stderr)
        exit(1)
    if args.outputdir and os.path.exists(args.outputdir):
        print(F"ERROR: output directory '{args.outputdir}'", file=sys.stderr)
        exit(1)
    if args.timeout < 0:
        args.timeout = None
    return args.calibrationdir, args.inputdir, args.outputdir, args.timeout

def get_input_image_names(inputdir):
    path_to_search = os.path.join(inputdir, '*.jpg')
    images = glob.glob(path_to_search)
    images.sort()
    return images

def main():
    calibrationdir, inputdir, outputdir, timeout = parse()
    print(f"Retrieving calibration parameters from '{calibrationdir}' ...", end='')
    calibration_img_width, calibration_img_height, calibration_mtx, calibration_dist = load_calibration_parameters(calibrationdir)
    print("DONE!")

    print(f"Retrieving input image files from '{inputdir}' ...", end='')
    images = get_input_image_names(inputdir)
    print("DONE!")
    print(f"Found {len(images)} images")

    # if output dir available, store undistorted images inside
    store_or_show_undistorted_images(pic_dir=inputdir, outdir=outputdir,
        calibration_mtx=calibration_mtx, calibration_dist=calibration_dist,
        waitKeyTimeout=timeout)

if __name__ == "__main__":
    main()


