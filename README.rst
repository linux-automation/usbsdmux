Welcome to usbsdmux
===================

|license|

Purpose
-------
This software is used to control a special piece of hardware called usb-sd-mux from the command line or python.

The usb-sd-mux is build around a `Microchip USB2642 <http://www.microchip.com/wwwproducts/en/USB2642>`_ card reader. Thus most of this software deals with interfacing this device using Linux ioctls().

This software is aimed to be used with `Labgrid <https://github.com/labgrid-project/labgrid>`_. But it can also be used stand-alone or in your own applications.

High-Level Functions
--------------------
usbsdmux provides the following functions:

* Multiplexing the SD-Card to either DUT, Host or disconnect with :code:`usbsdmux`
* Writing the Configuration-EEPROM of the USB2642 from the command line to customize the representation of the USB device: :code:`usbsdmux-configure`


Low-Level Functions
-------------------
Under the hood this tool provides interfaces to access the following features of the Microchip USB2642:

* Accessing the auxiliary I2C bus with write and write-read transactions with up to 512 bytes of payload using a simple python interface.
* Writing an I2C Configuration-EEPROM on the configuration I2C.
  This is done using an undocumented command that was reverse-engineered from Microchip's freely available EOL-Tools.

Using as root
-------------
If you just want to try the USB-SD-Mux (or maybe if it is just ok for you) you
can just use :code:`usbsdmux` as root.

If you have installed this tool inside a virutalenv you can just call the
shell-wrapper with something like
:code:`sudo /path/to/virtualenv/bin/usbsdmux /dev/sg1 DUT`.


Using as non-root user
----------------------
Access to /dev/sg* needs the `CAP_SYS_RAWIO <http://man7.org/linux/man-pages/man7/capabilities.7.html>`_. By default all processes created by root gain this capability.

Since you do not want to give this capability to the Python interpreter you

* either need to call the scripts as root
* or use the systemd-service.

The systemd-service is intended to be used with socket-activation.
The service is present inside :code:`usbsdmux-service`.
To use this service from a non-root user call something like
:code:`usbsdmux -c /dev/sg1 DUT`.

The systemd-units provided in :code:`contrib/systemd/` show an example of how to
set up the service with systemd and socket-activation.


Reliable names for the USB-SD-Mux
---------------------------------

A USB-SD-Mux comes with a pre-programmed serial that is also printed on the
device itself. With the udev-rule in :code:`contib/udev/99-usbsdmux.rules`
the sg-device for every USB-SD-Mux is linked to a device in
:code:`/dev/usb-sd-mux/id-*`.

This makes sure you can access a USB-SD-Mux with the same name - independent
of the order they are connected or the USB or the USB-topology.

ToDo
----

* Access to /dev/sg* needs the
  `CAP_SYS_RAWIO <http://man7.org/linux/man-pages/man7/capabilities.7.html>`_.
  The service should drop all not needed capabilities after it is started.


.. |license| image:: https://img.shields.io/badge/license-LGPLv2.1-blue.svg
    :alt: LGPLv2.1
    :target: https://raw.githubusercontent.com/pengutronix/usb-sd-mux-ctl/master/LICENSE
