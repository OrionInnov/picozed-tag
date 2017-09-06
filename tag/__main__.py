#!/usr/bin/env python

import argparse

from .tag import main as main_tag


def main():

    # argparse
    parser = argparse.ArgumentParser(description="Configure and execute the anchor daemon.")
    parser.add_argument("-t", "--tag-num", type=int, required=True, help="bit set to transmit")
    parser.add_argument("-b", "--bandwidth", type=int, default=int(50e6), help="bandwidth")
    parser.add_argument("-s", "--samp-rate", type=int, default=int(40e6), help="sample rate")
    parser.add_argument("-c", "--center-freq", type=long, default=long(2.462e9), help="center frequency")
    parser.add_argument("-p", "--period", type=float, default=0.0012, help="inverse of blink rate")

    # parse arguments
    args = parser.parse_args()

    # call appropriate daemon
    main_tag(args)


if __name__ == "__main__":
    main()
