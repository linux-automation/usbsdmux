#!/usr/bin/env python3

import fastentrypoints

from setuptools import setup

setup(
    name="usbsdmux",
    version="0.1.5",
    description="Tool to control an usb-sd-mux from the command line",
    packages=['usbsdmux'],
    entry_points={
        'console_scripts': [
            'usbsdmux = usbsdmux.__main__:main',
            'usbsdmux-configure = usbsdmux.usb2642eeprom:main',
            'usbsdmux-service = usbsdmux.service:main',
        ]
    },
)
