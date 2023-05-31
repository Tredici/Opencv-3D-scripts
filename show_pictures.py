
# simply take a directory and show all the images inside

import cv2
import timeit
import os
import datetime
import sys
import argparse
import glob
import re

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("indir", help="Path to directory containing pics to be shown")
    return parser

def parse():
    args = get_parser().parse_args()
    if not os.path.isdir(args.indir):
        print(f"ERROR: missing directory '{args.indir}'", file=sys.stderr)
        exit(1)
    return args.indir

def get_images(indir):
    path_to_search = os.path.join(indir, '*.jpg')
    images = glob.glob(path_to_search)
    return images

# commands available to the user
def display_commands():
    print("Commands:")
    print('\t', "q", "=>", "Quit")
    print('\t', "a", "=>", "Go to next image")
    print('\t', "z", "=>", "Go to previous image")
    print()

def main():
    indir = parse()
    print(f"Examining folder '{indir}'...")
    images = get_images(indir)
    imgcnt = len(images)
    print(f"Found {imgcnt} images")
    if imgcnt == 0:
        print(f"ERROR: no image found!")
        exit(1)
    print()
    display_commands()

    idx = 0
    changed = True
    while True:
        if changed:
            changed = False
            imfile = images[idx]
            imname = os.path.dirname(imfile)
            imtitle = f"[{idx+1}/{imgcnt}] {imname}"
            mat = cv2.imread(imfile)
            cv2.imshow(imtitle, mat)
        key = cv2.waitKey(0)

        if key == ord('q'):
            break
        elif key == ord('a'):
            changed = True
            idx = (idx+1)%imgcnt
        elif key == ord('z'):
            changed = True
            idx = (idx-1)%imgcnt

        if changed:
            cv2.destroyWindow(imtitle)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

