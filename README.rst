Welcome to usbsdmux
===================

|license|
|pypi|

Purpose
-------
This software is used to control a special piece of hardware called usb-sd-mux from the command line or python.

The usb-sd-mux is build around a `Microchip USB2642 <http://www.microchip.com/wwwproducts/en/USB2642>`_ card reader. Thus most of this software deals with interfacing this device using Linux ioctls().

This software is aimed to be used with `Labgrid <https://github.com/labgrid-project/labgrid>`_. But it can also be used stand-alone or in your own applications.

High-Level Functions
--------------------
usbsdmux provides the following functions:

* Multiplexing the SD-Card to either DUT, Host or disconnect with ``usbsdmux``
* Writing the Configuration-EEPROM of the USB2642 from the command line to customize the representation of the USB device: ``usbsdmux-configure``


Low-Level Functions
-------------------
Under the hood this tool provides interfaces to access the following features of the Microchip USB2642:

* Accessing the auxiliary I2C bus with write and write-read transactions with up to 512 bytes of payload using a simple python interface.
* Writing an I2C Configuration-EEPROM on the configuration I2C.
  This is done using an undocumented command that was reverse-engineered from Microchip's freely available EOL-Tools.

Quickstart
----------

Create and activate a virtualenv for usbsdmux:

.. code-block:: bash

   $ virtualenv -p python3 venv
   $ source venv/bin/activate

Install usbsdmux into the virtualenv:

.. code-block:: bash

   $ pip install usbsdmux

Now you can run ``usbsdmux -h`` to get a list of possible
command invocations:

.. code-block:: text

   $ usbsdmux -h
   usage: usbsdmux [-h] SG {get,dut,client,host,off}

   positional arguments:
     SG                    /dev/sg* to use
     {get,dut,client,host,off}
			   Action:
			   get - return selected mode
			   dut - set to dut mode
			   client - set to dut mode (alias for dut)
			   host - set to host mode
			   off - set to off mode

   optional arguments:
     -h, --help            show this help message and exit


Using as root
-------------
If you just want to try the USB-SD-Mux (or maybe if it is just ok for you) you
can just use ``usbsdmux`` as root.

If you have installed this tool inside a virtualenv you can just call the
shell-wrapper along with the appropriate `/dev/sg*` device path:

.. code-block:: bash

   sudo /path/to/virtualenv/bin/usbsdmux /dev/sg0 dut
   sudo /path/to/virtualenv/bin/usbsdmux /dev/sg0 host

Reliable names for the USB-SD-Mux
---------------------------------

A USB-SD-Mux comes with a pre-programmed serial that is also printed on the
device itself. With the udev-rule in ``contib/udev/99-usbsdmux.rules``
the sg-device for every USB-SD-Mux is linked to a device in
``/dev/usb-sd-mux/id-*``.

This makes sure you can access a USB-SD-Mux with the same name - independent
of the order they are connected or the USB or the USB-topology.

You can get a list of connected USB-SD-Muxes, based on their unique serial numbers,
by listing the contents of the ``/dev/usb-sd-mux/`` directory:

.. code-block:: bash

    $ ls -l /dev/usb-sd-mux/
    total 0
    lrwxrwxrwx 1 root root 6 Mar 31 11:21 id-000000000042 -> ../sg3
    lrwxrwxrwx 1 root root 6 Mar 27 00:33 id-000000000078 -> ../sg2
    lrwxrwxrwx 1 root root 6 Mar 24 09:51 id-000000000378 -> ../sg1

Troubleshooting
---------------

* Some single board computers, especially Raspberry Pi model 4s, do not work with
  new/fast micro SD cards, due to drive strength issues at high frequencies.
  Use old and slow micro SD cards with these devices.
  Another workaround is the replacement of resistors ``R101`` and ``R102`` with 0Ω
  parts. This modifications does however void the EMC compliance statement provided
  by the Linux Automation GmbH.
* Some usecases, like hard to reach connectors or full-size SD cards, necessitate the
  use of adapters or extension cables, leading to the same drive strength issues
  and require the same workarounds as documented above.
* In order for the ``/dev/sg*`` device to appear the ``sg`` kernel module needs to be loaded
  into the kernel. This is usually done automatically by ``udev`` once the USB-SD-Mux is connected.
  To manually load the kernel module run ``sudo modprobe sg``.

.. |license| image:: https://img.shields.io/badge/license-LGPLv2.1-blue.svg
    :alt: LGPLv2.1
    :target: https://raw.githubusercontent.com/linux-automation/usbsdmux/master/COPYING

.. |pypi| image:: https://img.shields.io/pypi/v/usbsdmux.svg
    :alt: pypi.org
    :target: https://pypi.org/project/usbsdmux
