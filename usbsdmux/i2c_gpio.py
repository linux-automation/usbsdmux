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

from abc import ABC

from .usb2642 import Usb2642


class I2cGpio(ABC):
    # Registers inside the supported GPIO expanders
    _register_inputPort = 0x00
    _register_outputPort = 0x01
    _register_polarity = 0x02
    _register_configuration = 0x03

    # Values for the configuration register
    _direction_output = 0
    _direction_input = 1

    def __init__(self, sg):
        """
        Arguments:
        sg -- /dev/sg* to use.
        """
        self._usb = Usb2642(sg)

    def get_usb(self):
        return self._usb

    def _write_register(self, register, value):
        """
        Writes a register on the GPIO-expander with a given value.
        """
        self._usb.write_to(self._I2cAddr, [register, value])

    def _read_register(self, addr):
        """
        Returns a register of the GPIO-expander.
        """
        return self._usb.write_read_to(self._I2cAddr, [addr], 1)[0]

    def set_pin_to_output(self, pins):
        """
        Sets the corresponding pins as outputs.

        Arguments:
        pins -- Combination of I2cGpio.gpio_*
        """
        direction = self._read_register(self._register_configuration)
        direction = (direction & ~pins) & 0xFF
        self._write_register(self._register_configuration, direction)

    def set_pin_to_input(self, pins):
        """
        Sets the corresponding pins as inputs.

        Arguments:
        pins -- Combination of I2cGpio.gpio_*
        """
        direction = self._read_register(self._register_configuration)
        direction = direction | pins
        self._write_register(self._register_configuration, direction)

    def get_gpio_config(self):
        """
        Returns the state of the configuration register.
        """
        return self._read_register(self._register_configuration)

    def get_input_values(self):
        """
        Reads the value currently present on the port from the input register.
        """
        return self._read_register(self._register_inputPort)

    def output_values(self, values: int, bitmask: int = 0xFF):
        """
        Writes the given values to the GPIO-expander.
        Pins configured as Inputs are not affected by this.

        Arguments:
        values -- Combination of I2cGpio.gpio_*
        bitmask -- Only update bits in the register that are '1' in the bitmask
        """

        if bitmask == 0xFF:
            # trivial case: Let's just write the value
            self._write_register(self._register_outputPort, values)
        else:
            # complex case: Let's do a read-modify-write
            val = self._read_register(self._register_outputPort)
            val = (val & ~bitmask) & 0xFF  # reset masked bits
            val = val | (values & bitmask)  # set bits set in values and bitmask
            self._write_register(self._register_outputPort, val)


class Pca9536(I2cGpio):
    """
    Interface to control a Pca9536 that is connected to the auxiliary-I2C of a
    Microchip USB2642.
    """

    # The PCA9536 I2C slave Address in 7-Bit Format
    _I2cAddr = 0b100_0001

    gpio_0 = 0x01
    gpio_1 = 0x02
    gpio_2 = 0x04
    gpio_3 = 0x08


class Tca6408(I2cGpio):
    """
    Interface to control a TCA6408 that is connected to the auxiliary-I2C of a
    Microchip USB2642.
    """

    # The TCA6408 I2C slave Address in 7-Bit Format
    _I2cAddr = 0b010_0000

    gpio_0 = 0x01
    gpio_1 = 0x02
    gpio_2 = 0x04
    gpio_3 = 0x08
    gpio_4 = 0x10
    gpio_5 = 0x20
    gpio_6 = 0x40
    gpio_7 = 0x80
