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

Clone the git repository:

.. code-block:: bash

   $ git clone https://github.com/pengutronix/usbsdmux.git

Create and activate a virtualenv for usbsdmux:

.. code-block:: bash

   $ virtualenv -p python3 venv
   $ source venv/bin/activate

Install usbsdmux into the virtualenv:

.. code-block:: bash

   $ python setup.py install

Now you can run ``usbsdmux`` command by giving the appropriate /dev/sg* device,
e.g.:

.. code-block:: bash

   $ usbsdmux /dev/sg1 dut
   $ usbsdmux /dev/sg1 host

Using as root
-------------
If you just want to try the USB-SD-Mux (or maybe if it is just ok for you) you
can just use ``usbsdmux`` as root.

If you have installed this tool inside a virtualenv you can just call the
shell-wrapper with something like
``sudo /path/to/virtualenv/bin/usbsdmux /dev/sg1 DUT``.


Using as non-root user
----------------------
Access to /dev/sg* needs the `CAP_SYS_RAWIO <http://man7.org/linux/man-pages/man7/capabilities.7.html>`_. By default all processes created by root gain this capability.

Since you do not want to give this capability to the Python interpreter you

* either need to call the scripts as root
* or use the systemd-service.

The systemd-service is intended to be used with socket-activation.
The service is present inside ``usbsdmux-service``.

The systemd-units provided in ``contrib/systemd/`` show an example of how to
set up the service with systemd and socket-activation.
You may adapt and copy them into your machine's local systemd service folder
``/etc/systemd/system/``

To start the socket unit and let it create the required socket path
(requires permissions), run::

  systemctl start usbsdmux.socket

Now you can use the ``usbsdmux`` tool from a non-root user by calling it with
the client ``-c`` argument, e.g.::

  usbsdmux -c /dev/sg1 DUT

If you use a non-standard socket path (i.e. not ``/tmp/sdmux.sock``) you also
need to explicitly set the socket path::

  usbsdmux -c -s /path/to/sock.file /dev/sg1 DUT

Reliable names for the USB-SD-Mux
---------------------------------

A USB-SD-Mux comes with a pre-programmed serial that is also printed on the
device itself. With the udev-rule in ``contib/udev/99-usbsdmux.rules``
the sg-device for every USB-SD-Mux is linked to a device in
``/dev/usb-sd-mux/id-*``.

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
