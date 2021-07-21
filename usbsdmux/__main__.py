#! /usr/bin/env python3

# SPDX-License-Identifier: LGPL-2.1-or-later

# Copyright (C) 2017 Pengutronix, Chris Fiege <entwicklung@pengutronix.de>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import argparse
import errno
import sys

from .usbsdmux import UsbSdMux

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("sg", metavar="SG", help="/dev/sg* to use")
    parser.add_argument(
        "mode",
        help="Action:\n"
             "get - return selected mode\n"
             "dut - set to dut mode\n"
             "client - set to dut mode (alias for dut)\n"
             "host - set to host mode\n"
             "off - set to off mode",
        choices=["get", "dut", "client", "host", "off"],
        type=str.lower)

    # These arguments were previously used for the client/service
    # based method to grant USB-SD-Mux access to non-root users.
    # The client/service model is no longer needed due to new udev
    # rules and a change to how the /dev/sg* devices are accessed.
    # Display a warning but do not fail when these are used so
    # existing scripts do not break and can be upgraded gracefully.
    parser.add_argument("-d", "--direct", help=argparse.SUPPRESS,
                        action="store_true", default=None)
    parser.add_argument("-c", "--client", help=argparse.SUPPRESS,
                        action="store_true", default=None)
    parser.add_argument("-s", "--socket", help=argparse.SUPPRESS,
                        default=None)

    args = parser.parse_args()

    if any(arg is not None for arg in (args.direct, args.client, args.socket)):
        print("usbsdmux: usage of -s/-c/-d arguments is deprecated "
              "as the service/client split is no longer required. "
              "Please upgrade your scripts to not supply either of these arguments",
              file=sys.stderr)

    ctl = UsbSdMux(args.sg)
    mode = args.mode.lower()

    try:
        if mode == "off":
            ctl.mode_disconnect()

        elif mode in ("dut", "client"):
            ctl.mode_DUT()

        elif mode == "host":
            ctl.mode_host()

        elif mode == "get":
            print(ctl.get_mode())

    except FileNotFoundError as fnfe:
        print(fnfe, file=sys.stderr)
        sys.exit(1)
    except PermissionError as perr:
        print(perr, file=sys.stderr)
        sys.exit(1)
    except OSError as ose:
        if ose.errno == errno.ENOTTY:
            # ENOTTY is raised when an error occured when calling an ioctl
            print(ose, file=sys.stderr)
            print(
                f"Does '{args.sg}' really point to an USB-SD-Mux?",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            raise ose


if __name__ == "__main__":
    main()
