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

import os
import time

from . import sd_regs
from .i2c_gpio import Pca9536, Tca6408


class UnknownUsbSdMuxRevisionException(Exception):
    pass


class NotInHostModeException(Exception):
    pass


def autoselect_driver(sg):
    """
    Create a new UsbSdMux with the correct driver for the device at /dev/<sg>

    Arguments:
    sg -- /dev/sg* to use
    """

    base_sg = os.path.realpath(sg)
    sg_name = os.path.basename(base_sg)
    model_filename = f"/sys/class/scsi_generic/{sg_name}/device/model"
    try:
        with open(model_filename, "r") as fh:
            model = fh.read().strip()
        if model == "sdmux HS-SD/MMC":
            return UsbSdMuxClassic(sg)
        elif model == "sdFST HS-SD/MMC":
            return UsbSdMuxFast(sg)
        else:
            raise UnknownUsbSdMuxRevisionException(
                f"Could not determine type of USB-SD-Mux. Found unknown SCSI model '{model}'."
            )
    except FileNotFoundError as e:
        raise UnknownUsbSdMuxRevisionException(
            f"Could not determine type of USB-SD-Mux. Does {model_filename} exist?"
        ) from e


class UsbSdMux:
    """
    Class to provide an interface for the multiplexer on an usb-sd-mux.
    """

    def __init__(self, sg):
        """
        Create a new UsbSdMux.

        Arguments:
        sg -- /dev/sg* to use
        """
        raise NotImplementedError()

    def get_mode(self):
        """
        Returns currently selected mode as string
        """
        raise NotImplementedError()

    def mode_disconnect(self, wait=True):
        """
        Will disconnect the Micro-SD Card from both host and DUT.

        Arguments:
        wait -- Command will block for some time until the voltage-supply of
        the sd-card is known to be close to zero
        """
        raise NotImplementedError()

    def mode_DUT(self, wait=True):
        """
        Switches the MicroSD-Card to the DUT.

        This Command will issue a disconnect first to make sure the SD-card
        has been properly disconnected from both sides and its supply was off.
        """
        raise NotImplementedError()

    def mode_host(self, wait=True):
        """
        Switches the MicroSD-Card to the Host.

        This Command will issue a disconnect first to make sure the SD-card
        has been properly disconnected from both sides and its supply was off.
        """
        raise NotImplementedError()

    def gpio_get(self, gpio):
        """
        Reads the value of gpio and returns "high" or "low"
        """
        raise NotImplementedError()

    def gpio_set_high(self, gpio):
        """
        Sets a gpio high.
        """
        raise NotImplementedError()

    def gpio_set_low(self, gpio):
        """
        Sets a gpio low.
        """
        raise NotImplementedError()

    def get_card_info(self):
        if self.get_mode() != "host":
            raise NotInHostModeException()

        result = {}

        scr = self._usb.read_scr()
        result["scr"] = sd_regs.SCR(scr.hex()).decode()

        cid = self._usb.read_cid()
        result["cid"] = sd_regs.CID(cid.hex()).decode()

        csd = self._usb.read_csd()
        result["csd"] = sd_regs.decode_csd(csd.hex()).decode()

        return result


class UsbSdMuxClassic(UsbSdMux):
    _DAT_enable = 0x00
    _DAT_disable = Pca9536.gpio_0

    _PWR_enable = 0x00
    _PWR_disable = Pca9536.gpio_1

    _select_DUT = Pca9536.gpio_2
    _select_HOST = 0x00

    _card_inserted = 0x00
    _card_removed = Pca9536.gpio_3

    def __init__(self, sg):
        self._pca = Pca9536(sg)
        self._usb = self._pca.get_usb()

    def get_mode(self):
        val = self._pca.get_input_values()

        # If the SD-Card is disabled, we do not need to check for the selected mode.
        # PWR_disable and DAT_disable are always switched at the same time.
        # Let's assume it is sufficient to check one of both.
        if val & self._PWR_disable:
            return "off"

        if val & self._select_DUT:
            return "dut"

        return "host"

    def mode_disconnect(self, wait=True):
        # Set the output registers to known values and activate them afterward
        self._pca.output_values(self._DAT_disable | self._PWR_disable | self._select_HOST | self._card_removed)
        self._pca.set_pin_to_output(Pca9536.gpio_0 | Pca9536.gpio_1 | Pca9536.gpio_2 | Pca9536.gpio_3)

        if wait:
            time.sleep(1)

    def mode_DUT(self, wait=True):
        self.mode_disconnect(wait)

        # switch selection to DUT first to prevent glitches on power and
        # data-lines
        self._pca.output_values(self._DAT_disable | self._PWR_disable | self._select_DUT | self._card_removed)

        # now connect data and power
        self._pca.output_values(self._DAT_enable | self._PWR_enable | self._select_DUT | self._card_removed)

    def mode_host(self, wait=True):
        self.mode_disconnect(wait)

        # The disconnect-command has already switched the card to the host.
        # Thus, we don't need to worry about glitches anymore.

        # now connect data and power
        self._pca.output_values(self._DAT_enable | self._PWR_enable | self._select_HOST | self._card_inserted)


class UsbSdMuxFast(UsbSdMux):
    _DAT_enable = 0x00
    _DAT_disable = Tca6408.gpio_2

    _PWR_enable = 0x00
    _PWR_disable = Tca6408.gpio_1

    _select_DUT = Tca6408.gpio_0
    _select_HOST = 0x00

    _card_inserted = 0x00
    _card_removed = Tca6408.gpio_3

    gpio0 = Tca6408.gpio_4
    gpio1 = Tca6408.gpio_5

    def __init__(self, sg):
        self._tca = Tca6408(sg)
        self._assure_default_state()
        self._usb = self._tca.get_usb()

    def _assure_default_state(self):
        # If the USB-SD-Mux has just been powered on, its default ("DUT") is defined by pull-resistors.
        # If we now do a "read-modify-write" without taking into account the external default, we will
        # lose this state.
        # So let's check if the GPIO-expander is in Power-On-Reset defaults.
        # If so, write the same state to the device - but with driven outputs.

        if self._tca.get_gpio_config() == 0xFF:
            # If all pins are still set to "input" we are in the default state.
            # Let's set an output value that matches this configuration and set the relevant pins to output.
            self._tca.output_values(self._DAT_enable | self._PWR_enable | self._select_DUT | self._card_removed)
            self._tca.set_pin_to_output(
                Tca6408.gpio_0 | Tca6408.gpio_1 | Tca6408.gpio_2 | Tca6408.gpio_3 | Tca6408.gpio_4 | Tca6408.gpio_5
            )

    def get_mode(self):
        val = self._tca.get_input_values()

        # If the SD-Card is disabled, we do not need to check for the selected mode.
        # PWR_disable and DAT_disable are always switched at the same time.
        # Let's assume it is sufficient to check one of both.
        if val & self._PWR_disable:
            return "off"

        if val & self._select_DUT:
            return "dut"

        return "host"

    def mode_disconnect(self, wait=True):
        self._tca.output_values(
            values=self._DAT_disable | self._PWR_disable | self._select_HOST | self._card_removed,
            bitmask=self._tca.gpio_0 | self._tca.gpio_1 | self._tca.gpio_2 | self._tca.gpio_3,
        )

        if wait:
            time.sleep(1)

    def mode_DUT(self, wait=True):
        self.mode_disconnect(wait)

        # switch selection to DUT first to prevent glitches on power and
        # data-lines
        self._tca.output_values(
            values=self._DAT_disable | self._PWR_disable | self._select_DUT | self._card_removed,
            bitmask=self._tca.gpio_0 | self._tca.gpio_1 | self._tca.gpio_2 | self._tca.gpio_3,
        )

        # now connect data and power
        self._tca.output_values(
            values=self._DAT_enable | self._PWR_enable | self._select_DUT | self._card_removed,
            bitmask=self._tca.gpio_0 | self._tca.gpio_1 | self._tca.gpio_2 | self._tca.gpio_3,
        )

    def mode_host(self, wait=True):
        self.mode_disconnect(wait)

        # The disconnect-command has already switched the card to the host.
        # Thus, we don't need to worry about glitches anymore.

        # now connect data and power
        self._tca.output_values(
            values=self._DAT_enable | self._PWR_enable | self._select_HOST | self._card_inserted,
            bitmask=self._tca.gpio_0 | self._tca.gpio_1 | self._tca.gpio_2 | self._tca.gpio_3,
        )

    @staticmethod
    def _map_gpio(gpio):
        if gpio == 0:
            return UsbSdMuxFast.gpio0
        elif gpio == 1:
            return UsbSdMuxFast.gpio1
        raise ValueError("Unknown GPIO")

    def gpio_get(self, gpio):
        """
        Reads the value of gpio and returns "high" or "low"
        """
        gpio = UsbSdMuxFast._map_gpio(gpio)
        val = self._tca.get_input_values()
        if val & gpio:
            return "low"
        return "high"

    def gpio_set_high(self, gpio):
        gpio = UsbSdMuxFast._map_gpio(gpio)
        self._tca.output_values(0x0, gpio)

    def gpio_set_low(self, gpio):
        gpio = UsbSdMuxFast._map_gpio(gpio)
        self._tca.output_values(gpio, gpio)
