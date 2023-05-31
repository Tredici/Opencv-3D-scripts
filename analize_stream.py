# Analyze the stream stored in .jpg pics inside the given directory


import cv2
import timeit
import os
import datetime
import sys
import glob
import argparse
import numpy as np
import re
import pprint

if __name__ == "__main__":
    import matplotlib
    import matplotlib.pyplot as plt


parser = argparse.ArgumentParser()
parser.add_argument("streamdir", help="Directory containing the stream")
parser.add_argument("-v", "--verbose", dest="verbose", default=False, action=argparse.BooleanOptionalAction, help="Output vebose")

def print_err(*args, **kwarks):
    print(*args, **kwarks, file=sys.stderr)
    exit(1)

# sample pics file name:
#   "stream-CAM2-2023-05-30_21-34-27.872104-pic-N000005-2023-05-30_21-34-28.035452.jpg"

def parse():
    args = parser.parse_args()
    if not os.path.exists(args.streamdir):
        print_err(f"ERROR: missing directory '{args.streamdir}'")
    return args.streamdir, args.verbose

# get stream picture as ordered list of file names
def get_stream_metadata(streamdir):
    search_path = os.path.join(streamdir, "*.jpg")
    images = glob.glob(search_path)
    if len(images) == 0:
        print_err(f"ERROR: no .jpg found inside '{streamdir}'")
    images.sort()
    f = os.path.basename(images[0]) # first filename took as reference 
    # ensure all picture are from the same stream
    # re with lookhaed assertion:
    #   https://docs.python.org/3/library/re.html
    m = re.match('^stream-(?P<camID>\w+)-(?P<streamtime>.+)(?=-pic-)', f)
    streamname = m.string[m.start():m.end()]
    bad = list(filter(lambda f: not f.startswith(streamname), map(os.path.basename, images)))
    if len(bad) > 0:
        print_err()
    streamtime = datetime.datetime.strptime(m.group('streamtime'), '%Y-%m-%d_%H-%M-%S.%f')
    # extract ID of the camera
    camID = m.groups('camID')[0]

    ## position of the first char after the '-pic-' part of the regex
    #new_begin = m.end()+len('-pic-')

    # extract metadata associated with images
    remd = re.compile(f"^(?>{streamname}-pic-)N"+"(?P<picNum>\d+)-(?P<picTime>.+)\.jpg$")
    imgdata = list(
        map(lambda t: {
                        "path": t[0],
                        "basename": os.path.basename(t[0]),
                        "picNum": t[1].group('picNum')[0],
                        "picTimeStr": t[1].groups('picTime')[1],
                        "picTime": datetime.datetime.strptime(t[1].groups()[1], '%Y-%m-%d_%H-%M-%S.%f'),
                        "fileSize": os.path.getsize(t[0])
                    },
        map(lambda t: (t[0], remd.match(t[1])),
        map(lambda imgpath: (imgpath, os.path.basename(imgpath)),
            images)
        ))
    )

    return {
        "camID": camID,
        "streamDir": os.path.join(os.getcwd(), streamdir),
        "streamName": streamname,
        "streamTime": streamtime,
        "images": images,
        "imageCount": len(images),
        "imgdata": imgdata,
    }


# extract timestamps in which pics have been captured
def get_pic_times(metadata: dict) -> list[datetime.datetime]:
    imgdata = metadata["imgdata"]
    pictimes = list(map(lambda x: x['picTime'], imgdata))
    return pictimes


# get interarrival delta to compute distribution
def calculate_inter_arrival_times(pictimes: list[datetime.datetime]) -> list[datetime.timedelta]:
    # do not modify original
    pictimes = pictimes.copy()
    pictimes.sort(reverse=False)
    inter_arrival_times = []
    for idx in range(1,len(pictimes)):
        inter_arrival_times.append( pictimes[idx] - pictimes[idx-1] )
    return inter_arrival_times

# put time origin in 0
def calculate_delay_from_first(pictimes: list[datetime.datetime], first: None | datetime.datetime = None) -> list[datetime.timedelta]:
    # do not modify original
    pictimes = pictimes.copy()
    pictimes.sort(reverse=False)
    # difference from first?
    if first is None:
        first = pictimes[0]
    ans = []
    for t in pictimes:
        ans.append(t - first)
    return ans

# get timedelta in milliseconds (as float)
def timedelta2float_ms(deltas: list[datetime.timedelta]) -> list[float]:
    ans = list(map(lambda td: td / datetime.timedelta(milliseconds=1), deltas))
    return ans


def main():
    matplotlib.use('TKAgg')
    #matplotlib.use('WebAgg')

    streamdir, verbose = parse()
    print(f"Examining folder '{streamdir}' ...")

    metadata = get_stream_metadata(streamdir)

    print("Result of the analysis:")
    if verbose:
        pp =  pprint.PrettyPrinter(depth=4)
        pp.pprint(metadata)
    else:
        print("\t", "")
        print('\t', "camID",      '\t=>', metadata["camID"])
        print('\t', "streamDir",  '\t=>', metadata["streamDir"])
        print('\t', "streamName", '\t=>', metadata["streamName"])
        print('\t', "streamTime", '\t=>', metadata["streamTime"])
    print()
    print('\t', "imageCount", '\t=>', metadata["imageCount"])
    print('\t', "total stream size", '\t=>', f'{sum(map(lambda x: x["fileSize"], metadata["imgdata"])):,} bytes')
    # compute average time difference between consecutive images
    imgdata = metadata["imgdata"]
    # img arrival times
    pictimes = get_pic_times(metadata)

    # see how interarrival times are distributed
    inter_arrival_times = calculate_inter_arrival_times(pictimes)
    inter_arrival_times_float = timedelta2float_ms(inter_arrival_times)

    # see if arrival rate is "stable" (no random wait)
    # derivative should seem constant
    delay_from_first = calculate_delay_from_first(pictimes)
    delay_from_first_float = timedelta2float_ms(delay_from_first)

    # generate figures
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(12, 4))
    ax0.hist(inter_arrival_times_float)
    ax1.plot(list(range(len(delay_from_first_float))), delay_from_first_float)

    plt.show()


if __name__ == "__main__":
    main()
