#! /usr/bin/env python3

from .usbsdmux import UsbSdMux
import argparse
import sys, errno
import json
import socket

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("sg", help="/dev/sg* to use")
    parser.add_argument(
        "mode",
        help="mode to switch to",
        choices=["dut", "host", "off", "client"],
        type=str.lower)
    parser.add_argument(
        "-c",
        "--client",
        help="Run in client mode with socket /tmp/sdmux.sock",
        action="store_true",
        default=False)
    parser.add_argument(
        "-s",
        "--socket",
        help="Run in client mode with given socket.",
        default="/tmp/sdmux.sock")

    args = parser.parse_args()

    if args.client is True or args.socket is not None:
        # socket mode

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        sock.connect(args.socket)
        payload = dict()
        payload["mode"] = args.mode
        payload["sg"] = args.sg
        sock.send(json.dumps(payload).encode())
        print(sock.recv(4096).decode())
        sock.close()

    else:
        # standalone mode

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
