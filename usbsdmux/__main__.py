#! /usr/bin/env python3

from .usbsdmux import UsbSdMux
import argparse

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("sg", help="/dev/sg* to use")
    parser.add_argument(
        "mode", help="mode to switch to. Can be {off, DUT, host}")

    args = parser.parse_args()

    ctl = UsbSdMux(args.sg)

    if args.mode.lower() == "off":
        ctl.mode_disconnect()

    if args.mode.lower() == "dut":
        ctl.mode_DUT()

    if args.mode.lower() == "host":
        ctl.mode_host()

if __name__ == "__main__":
    main()
