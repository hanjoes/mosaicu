import argparse

from processor import PNGProcessor


def process(args):
    # TODO: recognize file formats
    processor = PNGProcessor(args.pic)
    processor.spit_meta()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CLI controls how sync behaves')
    parser.add_argument('--pic',
                        required=True,
                        help='source folder if bi is set')

    args = parser.parse_args()
    process(args)
