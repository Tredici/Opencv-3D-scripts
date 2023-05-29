import numpy as np
import cv2 as cv
import glob
import sys
import os

# Tutorial:
#   https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html

# chessboard propierties
ROWS = 6
COLS = 9

search_dir = sys.argv[1]

# termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((ROWS*COLS,3), np.float32)
objp[:,:2] = np.mgrid[0:COLS,0:ROWS].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.


path_to_search = os.path.join(search_dir, '*.jpg')

images = glob.glob(path_to_search)

for fname in images:
    print(f"Processing image '{fname}'")

    img = cv.imread(fname)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Find the chess board corners
    ret, corners = cv.findChessboardCorners(gray, (COLS,ROWS), None)

    print("Found corners:", ret)

    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)
        corners2 = cv.cornerSubPix(gray,corners, (11,11), (-1,-1), criteria)
        imgpoints.append(corners2)
        # Draw and display the corners
        cv.drawChessboardCorners(img, (COLS,ROWS), corners2, ret)
        cv.imshow('img', img)
        cv.waitKey(5000)
    print("DONE!\n")

cv.destroyAllWindows()

print()
print("Calculate correction parameters:")
ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

for fname in images:
    print(f"Undistorting {fname}")
    img = cv.imread(fname)
    
    h, w = img.shape[:2]
    newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w,h), 1, (w,h))
    
    # undistort
    dst = cv.undistort(img, mtx, dist, None, newcameramtx)
    # crop the image
    x, y, w, h = roi
    dst = dst[y:y+h, x:x+w]

    img_und = np.zeros(img.shape, np.uint8)
    img_und[y:y+h, x:x+w] = dst
    comparison = np.concatenate((img, img_und), axis=0)
    comparison = cv.resize(comparison, tuple(map(lambda n:n//2, comparison.shape[0:2])))
    cv.imshow('Undistorted img', comparison)
    cv.waitKey(5000)
    #cv.imwrite('calibresult.png', dst)


