import numpy as np
import cv2 as cv
import glob
import sys
import os
import cv2
import os
import argparse
import re

# directory containing picture to locate picture to perform undistortion
chessdir = os.path.join(os.path.dirname(__file__), 'pics-2023-05-29_16-44-19-CALIBBOARD-OK')

def calculate_undistortion_params(chessdir):
    # chessboard size
    ROWS = 6
    COLS = 9
    # termination criteria
    criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((ROWS*COLS,3), np.float32)
    objp[:,:2] = np.mgrid[0:COLS,0:ROWS].T.reshape(-1,2)
    # Arrays to store object points and image points from all the images.
    objpoints = [] # 3d point in real world space
    imgpoints = [] # 2d points in image plane.
    # locate images
    path_to_search = os.path.join(chessdir, '*.jpg')
    images = glob.glob(path_to_search)
    for fname in images:
        img = cv.imread(fname)
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv.findChessboardCorners(gray, (COLS,ROWS), None)
        # If found, add object points, image points (after refining them)
        if ret == True:
            objpoints.append(objp)
            corners2 = cv.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
            imgpoints.append(corners2)
    ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
    return (ret, mtx, dist, rvecs, tvecs)

parser = argparse.ArgumentParser()
parser.add_argument("indir", help="Path to directory containing pics to be filtered")
parser.add_argument("outdir", help="Path to directory to store chosen pics inside, must NOT exist")

def main():
    args = parser.parse_args()
    indir = args.indir
    outdir = args.outdir
    if not os.path.isdir(indir):
        print(f"ERROR: directory '{indir}' does not exists! (Or it is not a directory.)", file=sys.stderr)
        exit(1)
        pass
    if os.path.exists(outdir):
        print(f"ERROR: path '{outdir}' already exists!", file=sys.stderr)
        exit(1)

    names = os.listdir(indir)
    jpg_names = filter(lambda path: re.match(pattern='.*(\.jpg)|(\.jpeg)^', string=path) is not None, names)
    jpg_paths = map(lambda jpg: os.path.join(indir, jpg), jpg_names)
    jpg_paths = list(jpg_paths)
    jpg_paths.sort()

    img_cnt = len(jpg_paths)
    if img_cnt == 0:
        print(f"ERROR: input dir '{indir}' is EMPTY! Content:", jpg_paths, file=sys.stderr)
        exit(1)

    print("[")
    for p in jpg_paths:
        print(f"\t'{p}'")
    print("]")

    print(f"Found {len(jpg_paths)} pictures")

    os.mkdir(outdir)
    print(f"Directory '{outdir}' created!")

    # calculate reconstruction parameters
    ret, mtx, dist, rvecs, tvecs = calculate_undistortion_params(chessdir)

    img_idx = 0
    for p in jpg_paths:
        img_idx += 1
        img = cv2.imread(p)
        img_name = os.path.basename(p)

        # load and undistort img
        h, w = img.shape[:2]
        newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
        # undistort
        dst = cv.undistort(img, mtx, dist, None, newcameramtx)
        # crop the image
        x, y, w, h = roi
        dst = dst[y:y+h, x:x+w]

        # show old and undistorted image
        img_und = np.zeros(img.shape, np.uint8)
        img_und[y:y+h, x:x+w] = dst
        comparison = np.concatenate((img, img_und), axis=0)
        comparison = cv.resize(comparison, tuple(map(lambda n:n//2, comparison.shape[0:2])))

        winname = f"[{img_idx}/{img_cnt}] Undistorted {img_name}"
        cv2.imshow(winname, comparison)
        cv.waitKey(0)
        cv2.destroyWindow(winname)

        # store undistorted image
        outpath = os.path.join(outdir, img_name)
        cv2.imwrite(outpath, dst)
        print("Saved", outpath)
        print()

    # Hadoop inspired termination
    with open(os.path.join(outdir, '_SUCCESS'), 'w'):
        pass

if __name__ == "__main__":
    main()
