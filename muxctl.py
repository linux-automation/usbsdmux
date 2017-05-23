#!/usr/bin/env python3

import argparse
import Pca9536
import time

class Muxctl(object):

    _DAT_enable = 0x00
    _DAT_disable = Pca9536.Pca9536._gpio_0

    _PWR_enable = 0x00
    _PWR_disable = Pca9536.Pca9536._gpio_1

    _select_DUT = Pca9536.Pca9536._gpio_2
    _select_HOST = 0x00

    _card_inserted = 0x00
    _card_removed = Pca9536.Pca9536._gpio_3

    def __init__(self, sg):
        self._pca = Pca9536.Pca9536(sg)

        # setting the output-values to defaults before enabling outputs on the GPIO-expander
        self.modeDisconnect(wait=False)

        # now enabling outputs
        self._pca.setPinToOutput(Pca9536.Pca9536._gpio_0 | Pca9536.Pca9536._gpio_1 | Pca9536.Pca9536._gpio_2 | Pca9536.Pca9536._gpio_3)

    def modeDisconnect(self, wait=True):
        """
        Will disconnect the Micro-SD Card from both host and DUT.

        Arugments:
        wait -- Command will block for some time until the voltage-supply of the sd-card is known to be close to zero
        """

        self._pca.outputValues(self._DAT_disable | self._PWR_disable | self._select_HOST | self._card_removed)

        time.sleep(1)


    def modeDUT(self, wait=True):
        """
        Switches the MicroSD-Card to the DUT.

        This Command will issue a disconnect first to make sure the the SD-card has been properly disconnected from both sides and it's supply was off.
        """

        self.modeDisconnect(wait)

        # switch selection to DUT first to prevent glitches on power and data-lines
        self._pca.outputValues(self._DAT_disable | self._PWR_disable | self._select_DUT | self._card_removed)

        # now connect data and power
        self._pca.outputValues(self._DAT_enable | self._PWR_enable | self._select_DUT | self._card_removed)

    def modeHost(self, wait=True):
        """
        Switches the MicroSD-Card to the Host.

        This Command will issue a disconnect first to make sure the the SD-card has been properly disconnected from both sides and it's supply was off.
        """

        self.modeDisconnect(wait)

        # the disconnect-command has already switched the card to the host. thus we don't need to worry about glitches anymore.

        # now connect data and power
        self._pca.outputValues(self._DAT_enable | self._PWR_enable | self._select_HOST | self._card_inserted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("sg", help="/dev/sg* to use")
    parser.add_argument("mode", help="mode to switch to. Can be {off, DUT, host}")

    args = parser.parse_args()

    ctl = Muxctl(args.sg)

    if args.mode.lower() == "off":
        ctl.modeDisconnect()

    if args.mode.lower() == "dut":
        ctl.modeDUT()

    if args.mode.lower() == "host":
        ctl.modeHost()

