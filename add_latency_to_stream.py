# Analyze the stream stored in .jpg pics inside the given directory


# rely on functions defined by analize_stream
from analize_stream import *
import shutil

parser = argparse.ArgumentParser()
parser.add_argument("streamdir", help="Directory containing the original stream")
parser.add_argument("outputdir", help="Directory to put modified stream in. MUST EXISTS! A new, per stream, subfolder is generated inside it")
parser.add_argument("delay_distribution", help="Probability distribution to be used, followed by its parameters (-h/--help for details)")


parser.add_argument("-v", "--verbose", dest="verbose", default=False, action=argparse.BooleanOptionalAction, help="Output vebose")


# given a fake_metadata dictionary (obtained via *DelayGenerator.generate_fake_metadata),
# create its folder and add its files
def create_delayed_sequence(fake_metadata):
    new_stream_dir = fake_metadata["streamDir"]
    os.mkdir(new_stream_dir)
    print(f"Created directory '{new_stream_dir}'")
    cwd = os.getcwd()
    for fkimg in fake_metadata["imgdata"]:
        src = os.path.join(cwd, fkimg["original"]["path"])
        dst = os.path.join(cwd, fkimg["path"])
        shutil.copyfile(src, dst)
    
    # Hadoop inspired termination
    with open(os.path.join(new_stream_dir, '_SUCCESS'), 'w'):
        pass

class DelayGenerator:
    # container_folder: folder in which the new delayed distribution
    # should be placed
    def __init__(self, container_folder: str | None = None) -> None:
        self.container_folder = container_folder
    def set_container_folder(self, container_folder):
        self.container_folder = container_folder
    def get_distribution_name(self) -> str:
        return self.__class__.delay_distribution_name
    def generate_fake_metadata(self, original_metadata: dict) -> dict:
        # the stream name is alwai the same
        original_stream_name = original_metadata["streamName"]

        # the folder created to store the new sequence has a
        # different name: it reports the info about the applied
        # delay distribution
        new_stream_dir = os.path.join(self.container_folder, f"{original_stream_name}-{self.get_distribution_str()}")

        new_imgdata = list(
            # add missing path - trick to update and return dictionary
            map(lambda d: d.update({"path": os.path.join(new_stream_dir, d["basename"])}) or d,
            # generate new fake item
            map(lambda t: {
                            "basename": f"{original_stream_name}-pic-N{t[0]['picNum']:06d}-{t[2]}.jpg",
                            "picNum": t[0]["picNum"],
                            "picTime": t[1],
                            "picTimeStr": t[2],
                            "fileSize": t[0]["fileSize"],
                            # delay introduced by generator
                            "addedDelay": t[3],
                            # reference to the original data
                            "original": t[0],
                        },
            # add also stringfied fake generation time
            map(lambda t: (t[0], t[0]["picTime"] + t[1], (t[0]["picTime"] + t[1]).strftime('%Y-%m-%d_%H-%M-%S.%f'), t[1]),
            # add fake delay to original sample
            map(lambda original: ((original.update({"picNum": int(original["picNum"])}) or original), self.generate_timedelta_delay()),
                original_metadata["imgdata"])
            )))
            )

        fake_metadata = {
            "camID": original_metadata["camID"],
            "streamDir": new_stream_dir,
            "streamName": original_stream_name,
            "streamTime": original_metadata["streamTime"],
            # path to new files data (not written yet)
            "images": list(map(lambda idata: idata["path"], new_imgdata)),
            # count is constant
            "imageCount": original_metadata["imageCount"],
            # updated data
            "imgdata": new_imgdata,
            # reference to old data
            "originalMetadata": original_metadata,
        }
        return fake_metadata
    # get delay as timedelta
    def generate_timedelta_delay(self) -> float:
        return self.generate_float_delay() * datetime.timedelta(milliseconds=1)
    # method returning a strin describing the applied distribution
    def get_distribution_str(self) -> str:
        raise NotImplementedError()
    # method called to get a random number generate accordingly the
    # underlaying distribution
    def generate_float_delay(self) -> float:
        raise NotImplementedError()


class ConstantDelayGenerator(DelayGenerator):
    delay_distribution_name = "const"
    def __init__(self, delay) -> None:
        super().__init__()
        self.delay = delay
    def get_distribution_str(self) -> str:
        return f"norm_{self.delay}"
    def generate_float_delay(self) -> float:
        return self.delay


class ExponentialDelayGenerator(DelayGenerator):
    delay_distribution_name = "exp"
    def __init__(self, mean) -> None:
        super().__init__()
        self.mean = mean
    def get_distribution_str(self) -> str:
        return f"exp_{self.mean}"
    def generate_float_delay(self) -> float:
        return np.random.exponential(self.mean)


class NormalDelayGenerator(DelayGenerator):
    delay_distribution_name = "exp"
    def __init__(self, mu, sigma) -> None:
        super().__init__()
        self.mean = mu
        self.sigma = sigma
    def get_distribution_str(self) -> str:
        return f"exp_{self.mu}_{self.sigma}"
    def generate_float_delay(self) -> float:
        return np.random.normal(self.mu, self.sigma)


# parse the parameter expressing the required delay distribution and
# return a callable to be used on the "metadata" object describing the
# original "sequence", to generate a new metadata object describing
# the new delayed sequence.
#
# N.B.: the metadata structure is the one returned by
#   "analize_stream.get_stream_metadata"
def parse_delay_distribution(delay_parameter: str, container_folder: str):
    delay_distribution = None

    if delay_parameter == '-h' or delay_parameter == '--help':
        print('\t', "const,delay_ms     constant delay added to each sample")
        print('\t', "exp,mean_ms        exponentially distributed delay added to each sample")
        print('\t', "norm,mu_ms,sig_ms  normally distributed delay added to each sample")

        exit(0)
    else:
        s = delay_parameter.split(',')
        if not 2 <= len(s) <= 3:
            print_err(f"Invalid paramenter 'delay_distribution': '{delay_parameter}'")
        dist_name = s[0]
        parameters = s[1:]
        if dist_name == "const" or dist_name == "constant":
            if len(parameters) != 1:
                print_err("ERROR: 'constant' distribution expect 1 parameter!\n" + f"Invalid paramenter 'delay_distribution': '{delay_parameter}'")
            delay = float(parameters[0])
            delay_distribution = ConstantDelayGenerator(delay=delay)
        elif dist_name == "exp" or dist_name == "exponential":
            if len(parameters) != 1:
                print_err("ERROR: 'exponential' distribution expect 1 parameter!\n" + f"Invalid paramenter 'delay_distribution': '{delay_parameter}'")
            mean_e = float(parameters[0])
            delay_distribution = ExponentialDelayGenerator(mean=mean_e)
        elif dist_name == "norm" or dist_name == "normal":
            if len(parameters) != 2:
                print_err("ERROR: 'normal' distribution expect 2 parameter!\n" + f"Invalid paramenter 'delay_distribution': '{delay_parameter}'")
            mu = float(parameters[0])
            sigma = float(parameters[1])
            delay_distribution = NormalDelayGenerator(mu=mu, sigma=sigma)
        else:
            print_err(f"Invalid paramenter 'delay_distribution': '{delay_parameter}'")

    delay_distribution.set_container_folder(container_folder)
    return delay_distribution


def parse():
    args = parser.parse_args()
    if not os.path.exists(args.streamdir):
        print_err(f"ERROR: missing directory '{args.streamdir}'")
    if not os.path.exists(args.outputdir):
        print_err(f"ERROR: output directory '{args.outputdir}' exists!")
    
    delay_generator = parse_delay_distribution(args.delay_distribution, args.outputdir)

    return args.streamdir, args.outputdir, delay_generator, args.verbose


def main():
    streamdir, outputdir, delay_generator, verbose = parse()
    print(f"Examining folder '{streamdir}' ... ", end='')
    metadata = get_stream_metadata(streamdir)
    print("DONE!", f"Found {metadata['imageCount']} images")
    print("Generating fake delayed sequence ... ", end='')
    fake_metadata = delay_generator.generate_fake_metadata(metadata)
    print("DONE!")
    if verbose:
        pp =  pprint.PrettyPrinter(depth=4)
        pp.pprint(fake_metadata)
    create_delayed_sequence(fake_metadata)

if __name__ == "__main__":
    main()
