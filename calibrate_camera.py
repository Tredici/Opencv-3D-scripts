
import cv2
import timeit
import os
import datetime
import sys
import argparse
import numpy as np
import glob
from undistort_folder import calculate_undistortion_params, show_undistorted_images

calibration_img_width_file = "calibration_img_width.npy"
calibration_img_height_file = "calibration_img_height.npy"
calibration_mtx_file = "calibration_mtx.npy"
calibration_dist_file = "calibration_dist.npy"

# default chessboard size
ROWS = 6
COLS = 9

basedir = os.path.dirname(__file__)

parser = argparse.ArgumentParser()
parser.add_argument("cameraId", help="Argument for cv2.VideoCapture(0)")
parser.add_argument("picdir", help="Directory in which selected frame will be put")
parser.add_argument("-r", "--resolution", dest="resolution", default=None, help="Argument for cv2.VideoCapture(0)")
parser.add_argument("-c", "--chessboard", dest="chessboard", default=None, help="Chessboard 'ROWS,COLS' size")

# STATS parameters
MEASURES_PER_STATS = 50
stats = []

def print_err(*args, **kwarks):
    print(*args, **kwarks, file=sys.stderr)
    exit(1)

# parse arguments
def parse():
    args = parser.parse_args()
    if args.resolution and len(args.resolution) > 0:
        args.resolution = tuple(map(int, args.resolution.split(',')))
        if len(args.resolution) != 2:
            print_err("Invalid parameter resolution:", args.resolution)
            exit(1)
    if args.chessboard and len(args.chessboard) > 0:
        args.chessboard = tuple(map(int, args.chessboard.split(',')))
        if len(args.chessboard) != 2:
            print_err("Invalid parameter chessboard:", args.chessboard)
            exit(1)
    else:
        args.chessboard = (ROWS, COLS)
    picdirname = f"CALIBRATION-{args.picdir}-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    picdirname = os.path.join(basedir, picdirname)
    if os.path.exists(picdirname):
        print_err(f"Invalid path '{picdirname}'")

    return args.cameraId, args.resolution, picdirname, args.chessboard

# commands available to the user
def display_commands():
    print("Commands:")
    print('\t', "q", "=>", "Quit capture and perform calibration")
    print("\t ' '", "=>", "get frame to be used for calibration")
    print()

# calculate and display stats
def statistics(measures: list[float]):
    count = len(measures)
    print(f"Measures: {count}")
    if count:
        sum = np.sum(measures)
        print("\t", "avg:", np.mean(measures))
        print("\t", "std:", np.std(measures))
        print("\t", "sum:", sum)
        print("\t", "min:", np.min(measures))
        print("\t", "max:", np.max(measures))
        print("\t", "Framerate:", count/sum)
        measures.clear()
    print()


# display capture properties
def camera_proprerties(vcap, new_resolution=None):
    ret, _ = vcap.read()
    if not ret:
        print("CANNOT ACCESS CAMERA! Exiting...", file=sys.stderr)
        exit(1)
    print("Camera stats:")
    if new_resolution:
        if not vcap.set(cv2.CAP_PROP_FRAME_WIDTH, new_resolution[0]):
            print_err("Cannot set Camera Width to", new_resolution[0])
        if not vcap.set(cv2.CAP_PROP_FRAME_HEIGHT, new_resolution[1]):
            print_err("Cannot set Camera Height to", new_resolution[1])
    width = vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print("\t", "width:", width)
    print("\t", "height:", height)
    print()


def store_img(picdirname, img):
    now = datetime.datetime.now()
    filename = f"pic-{now.strftime('%Y-%m-%d_%H-%M-%S.%f')}.jpg"
    filepath = os.path.join(picdirname, filename)
    cv2.imwrite(filepath, img)
    print()


def main():
    cameraId, resolution, picdirname, (cb_ROWS, cb_COLS) = parse()
    picdir = False
    print(f"cameraId: {cameraId}")
    print(f"Calibration images will be stored inside '{picdirname}'")
    print()

    vcap = cv2.VideoCapture(cameraId, cv2.CAP_ANY)
    camera_proprerties(vcap, new_resolution=resolution)

    img_title = f"Camera {cameraId}"

    display_commands()

    quit = False
    while True:
        start = timeit.default_timer()
        ret, frame = vcap.read()
        delta = timeit.default_timer() - start

        if not ret:
            print("Failed to read camera!", file=sys.stderr)
            quit = True
        else:
            # store delta only if it is valid
            stats.append(delta)

            cv2.imshow(img_title, frame)
            key = cv2.waitKey(1)
            if key == ord('q'):
                quit = True
            elif key == ord(' '):
                print("Caputed image for calibration")
                if not picdir:
                    # create directory
                    os.mkdir(picdirname)
                    picdir = True
                # save image
                store_img(picdirname, frame)

        if quit or key == ord('i') or len(stats) == MEASURES_PER_STATS:
            statistics(stats)

        # exit only after last stats have been published 
        if quit:
            cv2.destroyWindow(img_title)
            print("Quit")
            break

    print("Perform camera calibration")
    ret, mtx, dist, rvecs, tvecs = calculate_undistortion_params(picdirname, cb_ROWS, cb_COLS)
    show_undistorted_images(picdirname, mtx, dist)

    # store calibration parameters
    width = vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    np.save(os.path.join(picdirname, calibration_img_width_file),  width)
    np.save(os.path.join(picdirname, calibration_img_height_file), height)
    np.save(os.path.join(picdirname, calibration_mtx_file),        mtx)
    np.save(os.path.join(picdirname, calibration_dist_file),       dist)

    # Hadoop inspired termination
    with open(os.path.join(picdirname, '_SUCCESS'), 'w'):
        pass

if __name__ == "__main__":
    main()

