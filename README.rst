Welcome to usbsdmux
===================

|license|
|pypi|

Purpose
-------
This software is used to control a special piece of hardware called the
`USB-SD-Mux <https://www.linux-automation.com/en/products/usb-sd-mux.html>`_.
It can be used via the command line or as a Python library.

The USB-SD-Mux is built around a `Microchip USB2642 <http://www.microchip.com/wwwproducts/en/USB2642>`_ card reader. Thus most of this software deals with interfacing this device using Linux ioctls().

This software is aimed to be used with `Labgrid <https://github.com/labgrid-project/labgrid>`_. But it can also be used stand-alone or in your own applications.


Quickstart
----------

To get started with the ``usbsdmux`` tool you will first need to install the ``usbsdmux`` package.
There are different methods to doing this:

Installation from your Linux Distribution
  The easiest way to install the ``usbsdmux`` tool and stay somewhat up to date without having to deal with Python virtual environments.
  May not be available for your distribution and may be lacking in features because distributions ship older software versions.

Installation via pipx from PyPi
  Another way to install the ``usbsdmux`` from a pre-packaged source.
  Always installs the latest ``usbsdmux`` release, but needs to be kept up to date manually.
  Also needs a re-install when your systems Python version is updated.

  This installation method uses ``pipx`` to automate the Python virtual
  environment management.

Installation in a venv from PyPi
  This method is very similar to the ``pipx`` method,
  but manages the virtual environment manually instead of letting ``pipx`` manage it.

Installation from Source
  The way to go if you can not wait to test out new features.

Installation from Distribution Packages
```````````````````````````````````````

This tool is `packaged <https://packages.debian.org/search?keywords=usbsdmux&searchon=names&exact=1>`_ in Debian 12
(aka *bookworm*) and later.
The package ships the ``usbsdmux`` tool and the corresponding *udev* -rules.
So you can simply ``apt install usbsdmux`` and skip all installation steps below.

.. image:: https://repology.org/badge/vertical-allrepos/usbsdmux.svg
   :target: https://repology.org/project/usbsdmux/versions
   :alt: Packaging status
   :align: right

Packages also exist for `some other distributions <https://repology.org/project/usbsdmux/versions>`_.

Installation via pipx from PyPi Packages
````````````````````````````````````````

Install ``pipx`` via your Linux distributions package manager,
e.g.:

.. code-block:: bash

    $ sudo apt install pipx      # For Debian based distributions
    $ sudo pacman -S python-pipx # For Arch Linux based distributions

And follow the `pipx manual <https://github.com/pypa/pipx>`_ on how to add
``pipx``-installed software to your ``PATH``, e.g. by using ``pipx ensurepath``.

And finally install the ``usbsdmux`` package using ``pipx``:

.. code-block:: bash

    $ pipx install usbsdmux

Installation in a venv from PyPi Packages
`````````````````````````````````````````

Create and activate a Python virtual environment for the ``usbsdmux`` package:

.. code-block:: bash

   $ python3 -m venv venv
   $ source venv/bin/activate

Install the ``usbsdmux`` package into the virtual environment:

.. code-block:: bash

   $ python3 -m pip install usbsdmux

Installation From Source
````````````````````````

To get the latest and greatest you can also install the ``usbsdmux`` package
right from the git repository:

.. code-block:: bash

   $ git clone https://github.com/linux-automation/usbsdmux.git
   $ cd usbsdmux
   $ python3 -m venv venv
   $ source venv/bin/activate
   $ python3 -m pip install .

Usage
`````

Once installed you can run ``usbsdmux`` command with the ``-h`` flag to get a list of possible
command invocations:

.. code-block:: text

   $ usbsdmux -h
   usage: usbsdmux [-h] [--config CONFIG] [--json]
                   SG {get,dut,client,host,off,gpio,info} ...

   positional arguments:
     SG                    /dev/sg* to use
     {get,dut,client,host,off,gpio,info}
                           Supply one of the following commands to interact with the device
       get                 Read the current state of the USB-SD-Mux
       dut                 Switch to the DUT
       client              Switch to the DUT
       host                Switch to the host
       off                 Disconnect from host and DUT
       gpio                Manipulate a GPIO (open drain output only)
       info                Show information about the SD card

   options:
     -h, --help            show this help message and exit
     --config CONFIG       Set config file location
     --json                Format output as json. Useful for scripting.


Using as root
-------------
If you just want to try the USB-SD-Mux (or maybe if it is just ok for you) you
can just use the ``usbsdmux`` command as root.

If you have installed this tool inside a virtual environment you can just call the
shell-wrapper along with the appropriate `/dev/sg*` device path:

.. code-block:: bash

   $ sudo /path/to/venv/bin/usbsdmux /dev/sg0 dut
   $ sudo /path/to/venv/bin/usbsdmux /dev/sg0 host

If you encounter any issues using the USB-SD-Mux at this point consider consulting
the `Troubleshooting`_ section later in this README.


Using as normal user / Reliable names
-------------------------------------

The example udev-rule in ``contrib/udev/99-usbsdmux.rules`` serves two purposes:

* Allow users currently logged into the system and users in the
  ``plugdev`` group [1]_ to access connected USB-SD-Muxes.
* Create a reliable path in the filesystem to access specific
  USB-SD-Muxes based on their pre-programmed unique serial number.
  This is useful when multiple USB-SD-Muxes are connect to a system,
  as the enumeration-order, and thus the ``/dev/sg*`` numbering,
  may differ between reboots.
  The serial number is printed on a label attached to the device.

Users of a Debian based distribution [1]_ can install the udev rule
by cloning this repository and copying it to the appropriate location
and reloading the active udev rules:

.. code-block:: bash

   $ git clone "https://github.com/linux-automation/usbsdmux.git"
   $ sudo cp usbsdmux/contrib/udev/99-usbsdmux.rules /etc/udev/rules.d/
   $ sudo udevadm control --reload-rules

After reattaching the USB-SD-Mux you should get a list of connected USB-SD-Muxes,
based on their unique serial numbers, by listing the contents of
the ``/dev/usb-sd-mux/`` directory:

.. code-block:: bash

    $ ls -l /dev/usb-sd-mux/
    total 0
    lrwxrwxrwx 1 root plugdev 6 Mar 31 11:21 id-000000000042 -> ../sg3
    lrwxrwxrwx 1 root plugdev 6 Mar 27 00:33 id-000000000078 -> ../sg2
    lrwxrwxrwx 1 root plugdev 6 Mar 24 09:51 id-000000000378 -> ../sg1

.. [1] The ``plugdev`` group is used in Debian and Debian based distributions
       (like Ubuntu and Linux Mint) to grant access to pluggable gadgets.
       Depending on your Linux distribution you may want to create/use another
       group for this purpose and adapt the ``udev`` rule accordingly.


How it works
------------

High-Level Functions
````````````````````
The ``usbsdmux`` package provides the the following features:

* Muxing the SD-Card to either the DUT, Host or disconnecting it altogether via the ``usbsdmux`` command.
* Writing the Configuration-EEPROM of the USB2642 from the command line to customize the representation of the USB device via the ``usbsdmux-configure`` command.

Low-Level Functions
```````````````````
Under the hood this tool provides interfaces to access the following features of the Microchip USB2642:

* Accessing the auxiliary I2C bus with write and write-read transactions with up to 512 bytes of payload using a simple Python interface.
* Writing an I2C Configuration-EEPROM on the configuration I2C.
  This is done using an undocumented command that was reverse-engineered from Microchip's freely available EOL-Tools.


MQTT Statistics
---------------

This tool can be configured to send certain statistics to a MQTT broker.
To use this feature the `usbsdmux` util has to be installed with some
additional dependencies:

.. code-block:: bash

   $ python3 -m venv venv
   $ source venv/bin/activate
   $ python3 -m pip install "usbsdmux[mqtt]"

To enable this feature create a config file at ``/etc/usbsdmux.config``
or use ``--config`` to specify a file location.

See the example config file `usbsdmux.config <contrib/usbsdmux.config>`_
for available configuration options.


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


Contributing
------------

Thank you for considering a contribution to this project!
Changes should be submitted via a
`Github pull request <https://github.com/linux-automation/usbsdmux/pulls>`_.

This project uses the `Developer's Certificate of Origin 1.1
<https://developercertificate.org/>`_ with the same `process
<https://www.kernel.org/doc/html/latest/process/submitting-patches.html#sign-your-work-the-developer-s-certificate-of-origin>`_
as used for the Linux kernel:

  Developer's Certificate of Origin 1.1

  By making a contribution to this project, I certify that:

  (a) The contribution was created in whole or in part by me and I
      have the right to submit it under the open source license
      indicated in the file; or

  (b) The contribution is based upon previous work that, to the best
      of my knowledge, is covered under an appropriate open source
      license and I have the right under that license to submit that
      work with modifications, whether created in whole or in part
      by me, under the same open source license (unless I am
      permitted to submit under a different license), as indicated
      in the file; or

  (c) The contribution was provided directly to me by some other
      person who certified (a), (b) or (c) and I have not modified
      it.

  (d) I understand and agree that this project and the contribution
      are public and that a record of the contribution (including all
      personal information I submit with it, including my sign-off) is
      maintained indefinitely and may be redistributed consistent with
      this project or the open source license(s) involved.

Then you just add a line (using ``git commit -s``) saying:

  Signed-off-by: Random J Developer <random@developer.example.org>

using a known identity (sorry, no anonymous contributions).
