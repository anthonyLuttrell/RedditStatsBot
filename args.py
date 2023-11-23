import argparse


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-de",
                        "--debug",
                        help="Debug Mode, the parameter entered will be the subreddit that is used.")

    parser.add_argument("-d",
                        "--day",
                        help="Previous day will be the parameter entered.",
                        choices=range(1, 32),
                        default=0,
                        type=int)

    parser.add_argument("-p",
                        "--posts",
                        help="The number of posts that will be scanned.",
                        choices=range(1, 1001),
                        default=1000,
                        type=int)

    return parser.parse_args()
