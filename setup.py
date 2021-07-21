#!/usr/bin/env python3

from setuptools import setup
import fastentrypoints

setup(
    name="usbsdmux",
    version="0.2.1",
    author="Chris Fiege",
    author_email="python@pengutronix.de",
    license="LGPL-2.1-or-later",
    url="https://github.com/pengutronix/usbsdmux",
    description="Tool to control an usb-sd-mux from the command line",
    packages=['usbsdmux'],
    entry_points={
        'console_scripts': [
            'usbsdmux = usbsdmux.__main__:main',
            'usbsdmux-configure = usbsdmux.usb2642eeprom:main',
            'usbsdmux-service = usbsdmux.service:main',
        ],
    },
    classifiers=[
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)"
    ]
)
