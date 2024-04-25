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
import json
import sys

from .mqtthelper import Config, publish_info
from .sd_regs import decoded_to_text
from .usbsdmux import NotInHostModeException, UnknownUsbSdMuxRevisionException, autoselect_driver


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("sg", metavar="SG", help="/dev/sg* to use")

    parser.add_argument("--config", help="Set config file location", default=None)

    format_parser = parser.add_mutually_exclusive_group()
    format_parser.add_argument("--json", help="Format output as json. Useful for scripting.", action="store_true")

    subparsers = parser.add_subparsers(help="Supply one of the following commands to interact with the device")
    subparsers.required = True
    subparsers.dest = "mode"

    subparsers.add_parser("get", help="Read the current state of the USB-SD-Mux")
    subparsers.add_parser("dut", help="Switch to the DUT")
    subparsers.add_parser("client", help="Switch to the DUT")
    subparsers.add_parser("host", help="Switch to the host")
    subparsers.add_parser("off", help="Disconnect from host and DUT")

    parser_gpio = subparsers.add_parser("gpio", help="Manipulate a GPIO (open drain output only)")
    parser_gpio.add_argument("gpio", help="The GPIO to change", choices=[0, 1], type=int)
    parser_gpio.add_argument("action", help="What to do with the GPIO", choices=["low", "0", "high", "1", "get"])

    subparsers.add_parser("info", help="Show information about the SD card")

    # These arguments were previously used for the client/service
    # based method to grant USB-SD-Mux access to non-root users.
    # The client/service model is no longer needed due to new udev
    # rules and a change to how the /dev/sg* devices are accessed.
    # Display a warning but do not fail when these are used so
    # existing scripts do not break and can be upgraded gracefully.
    parser.add_argument("-d", "--direct", help=argparse.SUPPRESS, action="store_true", default=None)
    parser.add_argument("-c", "--client", help=argparse.SUPPRESS, action="store_true", default=None)
    parser.add_argument("-s", "--socket", help=argparse.SUPPRESS, default=None)

    args = parser.parse_args()

    if any(arg is not None for arg in (args.direct, args.client, args.socket)):
        print(
            "usbsdmux: usage of -s/-c/-d arguments is deprecated "
            "as the service/client split is no longer required. "
            "Please upgrade your scripts to not supply either of these arguments",
            file=sys.stderr,
        )

    config = Config(args.config)

    try:
        ctl = autoselect_driver(args.sg)
    except UnknownUsbSdMuxRevisionException as e:
        error_msg = str(e) + "\n" + f"Does {args.sg} really point to a USB-SD-Mux?"
        if args.json:
            print(json.dumps({"error-message": error_msg}))
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)
    mode = args.mode

    error_msg = None
    try:
        if mode == "off":
            ctl.mode_disconnect()
            if args.json:
                print(json.dumps({}))

        elif mode in ("dut", "client"):
            publish_info(ctl, config, args.sg, "client")

            ctl.mode_DUT()
            if args.json:
                print(json.dumps({}))

        elif mode == "host":
            ctl.mode_host()
            if args.json:
                print(json.dumps({}))

            publish_info(ctl, config, args.sg, "host")

        elif mode == "get":
            if args.json:
                print(json.dumps({"switch-state": ctl.get_mode()}))
            else:
                print(ctl.get_mode())

        elif mode == "gpio":
            if args.action == "get":
                if args.json:
                    print(json.dumps({"gpio-state": {"gpio": args.gpio, "state:": ctl.gpio_get(args.gpio)}}))
                else:
                    print(ctl.gpio_get(args.gpio))
            elif args.action in ["0", "low"]:
                ctl.gpio_set_low(args.gpio)
                if args.json:
                    print(json.dumps({}))
            elif args.action in ["1", "high"]:
                ctl.gpio_set_high(args.gpio)
                if args.json:
                    print(json.dumps({}))

        elif mode == "info":
            info = ctl.get_card_info()
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                print("\n".join(decoded_to_text(info["scr"])))
                print("\n".join(decoded_to_text(info["cid"])))
                print("\n".join(decoded_to_text(info["csd"])))

    except FileNotFoundError as fnfe:
        error_msg = str(fnfe)
    except PermissionError as perr:
        error_msg = str(perr)
    except OSError as ose:
        if ose.errno == errno.ENOTTY:
            # ENOTTY is raised when an error occurred when calling an ioctl
            error_msg = ose + "\n" + f"Does '{args.sg}' really point to a USB-SD-Mux?"
        else:
            raise ose
    except NotInHostModeException:
        error_msg = "Card information is only available in host mode."
    except NotImplementedError:
        error_msg = "This USB-SD-Mux does not support GPIOs."

    if error_msg:
        if args.json:
            print(json.dumps({"error-message": error_msg}))
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
