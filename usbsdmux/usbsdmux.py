#!/usr/bin/env python3

from .pca9536 import Pca9536
import time


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

    # setting the output-values to defaults before enabling outputs on the
    # GPIO-expander
    self.mode_disconnect(wait=False)

    # now enabling outputs
    self._pca.set_pin_to_output(
        Pca9536.gpio_0 | Pca9536.gpio_1 |
        Pca9536.gpio_2 | Pca9536.gpio_3)

  def mode_disconnect(self, wait=True):
    """
    Will disconnect the Micro-SD Card from both host and DUT.

    Arugments:
    wait -- Command will block for some time until the voltage-supply of
    the sd-card is known to be close to zero
    """

    self._pca.output_values(self._DAT_disable | self._PWR_disable |
                            self._select_HOST | self._card_removed)

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

