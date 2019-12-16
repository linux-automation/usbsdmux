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
        ],
    classifiers=[
        "License :: OSI Approved :: GNU Lesser General Public License v2.1 or later (LGPLv2.1+)"
    ]
    },
)
