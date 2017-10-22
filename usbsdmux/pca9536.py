#!/usr/bin/env python3

from .usb2642i2c import Usb2642I2C


class Pca9536(object):
  """
  Interface to control a Pca9536 that is connected to the auxiliary-I2C of a
  Microchip USB2642.
  """

  # The PCA9536 I2C Slave Address in 7-Bit Format
  _I2cAddr = 0x41

  # Registers inside the PCA9536
  _register_inputPort = 0x00
  _register_outputPort = 0x01
  _register_polarity = 0x02
  _register_configuration = 0x03

  gpio_0 = 0x01
  gpio_1 = 0x02
  gpio_2 = 0x04
  gpio_3 = 0x08

  _direction_output = 0
  _direction_input = 1

  def __init__(self, sg):
    """
    Create a new Pca9536-controller.

    Arguments:
    sg -- /dev/sg* to use.
    """
    self.sg = sg

    self._usb = Usb2642I2C(sg)

    # After POR all Pins are Inputs. This value will from now on mirror the
    # value of die _register_configuration
    self._directionMask = 0xFF

  def _write_register(self, register, value):
    """
    Writes a register on the Pca9536 with a given value.
    """

    self._usb.write_to(self._I2cAddr, [register, value])

  def set_pin_to_output(self, pins):
    """
    Sets the corresponding pins as outputs.

    Arguments:
    pins -- Combination of Pca9536.gpio_*
    """

    self._directionMask = self._directionMask & (~pins)
    self._write_register(self._register_configuration, self._directionMask)

  def set_pin_to_input(self, pins):
    """
    Sets the corresponding pins as inputs.

    Arguments:
    pins -- Combination of Pca9536.gpio_*
    """

    self._directionMask = self._directionMask | pins
    self._write_register(self._register_configuration, self._directionMask)

  def output_values(self, values):
    """
    Writes the given values to the GPIO-expander.
    Pins configured as Inputs are not affected by this.

    Arguments:
    values -- Combination of Pca9536.gpio_*
    """

    self._write_register(self._register_outputPort, values)
