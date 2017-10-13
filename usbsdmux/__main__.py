#! /usr/bin/env python3

from .usbsdmux import UsbSdMux
import argparse
import sys, errno

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("sg", help="/dev/sg* to use")
    parser.add_argument(
        "mode",
        help="mode to switch to",
        choices=["dut", "host", "off", "client"],
        type=str.lower)

    args = parser.parse_args()

    ctl = UsbSdMux(args.sg)

    if args.mode.lower() == "off":
        ctl.mode_disconnect()

    elif args.mode.lower() == "dut" or args.mode.lower() == "client":
        ctl.mode_DUT()

    elif args.mode.lower() == "host":
        ctl.mode_host()

    sys.exit()
if __name__ == "__main__":
    main()
