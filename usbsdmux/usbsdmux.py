#!/usr/bin/env python3

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

import time
from .pca9536 import Pca9536


class UsbSdMux(object):
  """
  Class to provide an interface for the multiplexer on an usb-sd-mux.
  """

  _DAT_enable = 0x00
  _DAT_disable = Pca9536.gpio_0

  _PWR_enable = 0x00
  _PWR_disable = Pca9536.gpio_1

  _select_DUT = Pca9536.gpio_2
  _select_HOST = 0x00

  _card_inserted = 0x00
  _card_removed = Pca9536.gpio_3

  def __init__(self, sg):
    """
    Create a new UsbSdMux.

    Arguments:
    sg -- /dev/sg* to use
    """
    self._pca = Pca9536(sg)

  def get_mode(self):
    """
    Returns currently selected mode as string
    """
    val = self._pca.read_register(1)[0]

    # If the SD-Card is disabled we do not need to check for the selected mode.
    # PWR_disable and DAT_disable are always switched at the same time.
    # Let's assume it is sufficient to check one of both.
    if val & self._PWR_disable:
      return "off"

    if val & self._select_DUT:
       return "dut"
    return "host"

  def mode_disconnect(self, wait=True):
    """
    Will disconnect the Micro-SD Card from both host and DUT.

    Arugments:
    wait -- Command will block for some time until the voltage-supply of
    the sd-card is known to be close to zero
    """

    # Set the output registers to known values and activate them afterwards
    self._pca.output_values(self._DAT_disable | self._PWR_disable |
                            self._select_HOST | self._card_removed)
    self._pca.set_pin_to_output(Pca9536.gpio_0 | Pca9536.gpio_1 |
                                Pca9536.gpio_2 | Pca9536.gpio_3)

    if wait:
        time.sleep(1)

  def mode_DUT(self, wait=True):
    """
    Switches the MicroSD-Card to the DUT.

    This Command will issue a disconnect first to make sure the the SD-card
    has been properly disconnected from both sides and it's supply was off.
    """

    self.mode_disconnect(wait)

    # switch selection to DUT first to prevent glitches on power and
    # data-lines
    self._pca.output_values(self._DAT_disable | self._PWR_disable |
                            self._select_DUT | self._card_removed)

    # now connect data and power
    self._pca.output_values(self._DAT_enable | self._PWR_enable |
                            self._select_DUT | self._card_removed)

  def mode_host(self, wait=True):
    """
    Switches the MicroSD-Card to the Host.

    This Command will issue a disconnect first to make sure the the SD-card
    has been properly disconnected from both sides and it's supply was off.
    """

    self.mode_disconnect(wait)

    # the disconnect-command has already switched the card to the host.
    # Thus we don't need to worry about glitches anymore.

    # now connect data and power
    self._pca.output_values(self._DAT_enable | self._PWR_enable |
                            self._select_HOST | self._card_inserted)

