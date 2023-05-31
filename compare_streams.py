
# given two different streams, compare their respective delays

# rely on functions defined by analize_stream
from analize_stream import *


parser = argparse.ArgumentParser()
parser.add_argument("streamdir_1", help="Directory containing the first stread")
parser.add_argument("streamdir_2", help="Directory containing the secpmd stread")
parser.add_argument("-v", "--verbose", dest="verbose", default=False, action=argparse.BooleanOptionalAction, help="Output vebose")

def parse():
    args = parser.parse_args()
    if not os.path.exists(args.streamdir_1):
        print_err(f"ERROR: missing directory '{args.streamdir_1}'")
    if not os.path.exists(args.streamdir_2):
        print_err(f"ERROR: missing directory '{args.streamdir_2}'")
    return args.streamdir_1, args.streamdir_2, args.verbose



def main():
    streamdir_1, streamdir_2, verbose = parse()

    metadata = get_stream_metadata(streamdir_1)
    metadata = get_stream_metadata(streamdir_2)

    
