#!/usr/bin/env python3

import Usb2642I2C

class Pca9536(object):
    """
    Interface to control a Pca9536 that is connected to the auxiliary-I2C of a Microchip USB2642.
    """

    """The PCA9536 I2C Slave Address in 7-Bit Format"""
    _I2cAddr = 0x41

    # Registers inside the PCA9536
    _register_inputPort = 0x00
    _register_outputPort = 0x01
    _register_polarity = 0x02
    _register_configuration = 0x03

    _gpio_0 = 0x01
    _gpio_1 = 0x02
    _gpio_2 = 0x04
    _gpio_3 = 0x08

    _direction_output = 0
    _direction_input  = 1

    def __init__(self, sg):
        """
        Create a new Pca9536-controller.

        Arguments:
        sg -- /dev/sg* to use.
        """
        self.sg = sg

        self._usb = Usb2642I2C.Usb2642I2C(sg)

        # After POR all Pins are Inputs. This value will from now on mirror the value of die _register_configuration
        self._directionMask = 0xFF

    def _writeRegister(self, register, value):
        """
        Writes a register on the Pca9536 with a given value.
        """

        self._usb.writeTo(self._I2cAddr, [register, value])

    def setPinToOutput(self, pins):
        """
        Sets the corresponding pins as outputs.

        Arguments:
        pins -- Combination of Pca9536._gpio_*
        """

        self._directionMask = self._directionMask & (~pins)
        self._writeRegister(self._register_configuration, self._directionMask)

    def setPinToInput(self, pins):
        """
        Sets the corresponding pins as inputs.

        Arguments:
        pins -- Combination of Pca9536._gpio_*
        """

        self._directionMask = self._directionMask | pin
        self._writeRegister(self._register_configuration, self._directionMask)


    def outputValues(self, values):
        """
        Writes the given values to the GPIO-expander.
        Pins configured as Inputs are not affected by this.

        Arguments:
        values -- Combination of Pca9536._gpio_*
        """

        self._writeRegister(self._register_outputPort, values)


if __name__ == "__main__":
    import time

    i2c = Pca9536("/dev/sg1")
    i2c.setPinToOutput(i2c._gpio_0 | i2c._gpio_1 | i2c._gpio_2 | i2c._gpio_3)
    for _ in range(100):
        i2c.outputValues(0x00)
        time.sleep(0.1)
        i2c.outputValues(0x04)
        time.sleep(0.1)



