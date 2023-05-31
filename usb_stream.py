
import cv2
import timeit
import os
import datetime
import sys
import argparse
import numpy as np

basedir = os.path.dirname(__file__)

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("cameraId", help="Argument for cv2.VideoCapture(0)")
    parser.add_argument("-r", "--resolution", dest="resolution", default=None, help="Argument for cv2.VideoCapture(0)")
    parser.add_argument("-p", "--picdir", dest="picdir", default=None, help="Directory in which selected frame will be put")
    return parser

# STATS parameters
MEASURES_PER_STATS = 50
stats = []

def print_err(*args, **kwarks):
    print(*args, **kwarks, file=sys.stderr)
    exit(1)

# parse arguments
def parse():
    args = get_parser().parse_args()
    if args.resolution and len(args.resolution) > 0:
        args.resolution = tuple(map(int, args.resolution.split(',')))
        if len(args.resolution) != 2:
            print("Invalid parameter resolution:", args.resolution, file=sys.stderr)
            exit(1)
    if args.picdir:
        dirname = os.path.dirname(args.picdir)
        basename = os.path.basename(args.picdir)
        picdirname = f"CAM{args.cameraId[-1]}-pics-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')}{'-' if basename else ''}{basename}"
        picdirname = os.path.join(dirname, picdirname)
    else:
        picdirname = f"pics-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')}"
    picdirname = os.path.join(basedir, picdirname)
    if os.path.exists(picdirname):
        print_err(f"Invalid path '{picdirname}'")

    return args.cameraId, args.resolution, picdirname

# commands available to the user
def display_commands():
    print("Commands:")
    print('\t', "q", "=>", "Quit")
    print('\t', "a", "=>", "Start capturing all the frames and storing them inside the given directory")
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


def get_camera_id(cameraId):
    return f"CAM{cameraId[-1]}"

def main():
    cameraId, resolution, picdirname = parse()
    print(f"cameraId: {cameraId}")
    print(f"Images will be saved inside: '{picdirname}'")
    print()
    # id used to recognize the camera capturing the images
    camId = get_camera_id(cameraId)

    # was picdir created?
    picdir = False

    vcap = cv2.VideoCapture(cameraId, cv2.CAP_ANY)
    # https://stackoverflow.com/questions/54249824/low-fps-by-using-cv2-videocapture
    # if not vcap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('m','j','p','g')):
    #     print_err("BUUUM")
    camera_proprerties(vcap, new_resolution=resolution)

    img_title = f"Camera {cameraId}"

    display_commands()

    # flag to exit the loop
    quit = False
    # flag to be used to capture all the frames
    capture_all = False
    # save "streams" (dequences of subsequentely captured images) together
    capture_all_dir = None
    # stream size
    stream_size = None
    while True:
        start = timeit.default_timer()
        ret, frame = vcap.read()
        delta = timeit.default_timer() - start
        # time reference to be used for stream construction
        now = datetime.datetime.now()

        stats.append(delta)

        if not ret:
            print("Failed to read camera!", file=sys.stderr)
            break
        else:
            cv2.imshow(img_title, frame)
            key = cv2.waitKey(1)
            if key == ord('q'):
                quit = True
            
            elif key == ord('a'):
                if not capture_all:
                    if not picdir:
                        os.mkdir(picdirname)
                        print(f"Created directory '{picdirname}'")
                        picdir = True
                    capture_all = True
                    stream_name = f"stream-{camId}-{now.strftime('%Y-%m-%d_%H-%M-%S.%f')}"
                    capture_all_dir = os.path.join(picdirname, stream_name)
                    os.mkdir(capture_all_dir)
                    stream_size = 0
                else:
                    capture_all = False
                    print(f"Stream '{stream_name}' terminated => final size: {stream_size}")

            if capture_all:
                stream_size += 1
                # randomly print infos about frames in stream
                if stream_size % 222 == 0:
                    print(f"Stream '{stream_name}': frame count: {stream_size}")
                # keep a reference to the stream name
                frame_name = f"{stream_name}-pic-N{stream_size-1:06d}-{now.strftime('%Y-%m-%d_%H-%M-%S.%f')}.jpg"
                outpath = os.path.join(capture_all_dir, frame_name)
                cv2.imwrite(outpath, frame)
                pass

        if quit or key == ord('i') or len(stats) == MEASURES_PER_STATS:
            statistics(stats)

        # exit only after last stats have been published 
        if quit:
            print("Quit")
            break

    # summary
    if stream_size is not None:
        print(f"Streams are available inside directory: '{picdirname}'")

if __name__ == "__main__":
    main()

