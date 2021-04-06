#! /usr/bin/env python3

# SPDX-License-Identifier: LGPL-2.1-or-later

# Copyright (C) 2021 Pengutronix, Leonard Göhrs <entwicklung@pengutronix.de>
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

"""
This service was intended as systemd-socket-activated unit and provided an
interface to the USB-SD-Mux without the need for root privileges.

Usage of this service became obsolete in new releases that changed the
way the /dev/sg* devices are accessed and that added new udev rules to
directly grant device access to the users.

This file is kept here to notify users that have set up a systemd service.
"""

import sys

def main():
    print("The usage of usbsdmux-service is deprecated.", file=sys.stderr)
    print("Access to USB-SD-Mux devices is now controlled by a new set of udev rules.", file=sys.stderr)
    print("Please delete/deactivate the service calling this command.", file=sys.stderr)
    exit(-1)
