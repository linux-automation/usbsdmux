Welcome to usbsdmux
===================


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


Access to /dev/sg*
------------------
Access to /dev/sg* needs the `CAP_SYS_RAWIO <http://man7.org/linux/man-pages/man7/capabilities.7.html>`_. By default all processes created by root gain this capability.

Since you do not want to give this capability to the Python interpreter you need to call the scripts as root.
A call to a shell-wrapper inside a virutalenv would look something like:
:code:`sudo /path/to/virtualenv/bin/usbsdmux /dev/sg1 DUT`
