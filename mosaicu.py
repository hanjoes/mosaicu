import argparse

from processor import PNGProcessor


def process(args):
    # TODO: recognize file formats
    processor = PNGProcessor(args.pic, args.output)
    # processor.get_metadata()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CLI controls how sync behaves')
    parser.add_argument('--pic',
                        required=True,
                        help='input picture')
    parser.add_argument('--output',
                        required=True,
                        help='output file name')

    args = parser.parse_args()
    process(args)
