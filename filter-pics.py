
import cv2
import timeit
import os
import datetime
import sys
import argparse
import re

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

    img_idx = 0
    for p in jpg_paths:
        img_idx += 1
        img = cv2.imread(p)
        img_name = os.path.basename(p)
        store = False
        winname = f"[{img_idx}/{img_cnt}] {img_name}"
        cv2.imshow(winname, img)
        while True:
            print(f"[{img_idx}/{img_cnt}]\t'{img_name}'\tStore [ỳ/n]? ", end='')
            key = cv2.waitKey(0)
            if key == ord('y'):
                store = True
                print('y', end='')
                outpath = os.path.join(outdir, img_name)
                cv2.imwrite(outpath, img)
                print('\tDONE!', end='')
                break
            if key == ord('n'):
                print('n', end='')
                break
            print()
        print()
        cv2.destroyWindow(winname)

    # Hadoop inspired termination
    with open(os.path.join(outdir, '_SUCCESS'), 'w'):
        pass

if __name__ == "__main__":
    main()


