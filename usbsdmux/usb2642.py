#!/usr/bin/env python3

# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2017 The USB-SD-Mux Authors

import ctypes
from time import sleep

from .ctypehelper import list_to_uint8_array
from .platform import IoctlFailed, execute_scsi_command

"""
This modules provides an interface to use the auxiliary and configuration
I2C-busses of the Microchip USB2642.
"""


class FrameLengthException(Exception):
    pass


class I2cTransactionFailed(Exception):
    pass


class SDTransactionFailed(Exception):
    pass


class Usb2642:
    """
    This class provides an interface to interact with devices on a Microchip
    USB2642 auxiliary I2C Bus and to write configuration to an EEPROM on the
    configuration I2C Bus.

    To do so it uses vendor specific SCSI-commands on the mass-storage device
    provided by the USB2642.
    Documentation to this behavior can be found in this documents:

    * 'Microchip: I2C_Over_USB_UserGuilde_50002283A.pdf' (Can be found in the
      (Windows-) software example provided on the components webpage)
    * The USB2641 datasheet
    * see http://www.microchip.com/wwwproducts/en/USB2642 for both documents

    Some more interesting links:

    * USB Mass Storage Bulk Transfer Profile Specification:
      http://www.usb.org/developers/docs/devclass_docs/usbmassbulk_10.pdf
    * Linux SG_IO ioctl() control structure:
      http://www.tldp.org/HOWTO/SCSI-Generic-HOWTO/sg_io_hdr_t.html
    * Denton Gentry's blog post about how to use the sg ioctl() from python:
      http://codingrelic.geekhold.com/2012/02/ata-commands-in-python.html
      This article uses it to make ATA-passthrough - beware that we do not use
      ATA-passthrough here.


    This class uses the /dev/sg* -Interface to access the SCSI-device even if no
    media is present.
    Make sure you have rw-rights :)
    """

    def __init__(self, sg):
        """
        Create a new USB2642-Interface wrapper.

        Arguments:
        sg -- The sg-device to use. E.g. "/dev/sg1"
        """
        self.sg = sg

    """
    This Opcode represents a vendor specific SCSI command.
    According to: 'Microchip: I2C_Over_USB_UserGuilde_50002283A.pdf' P.20
    """
    _USB2642SCSIOPCODE = 0xCF

    """
    This Vendor Action marks an I2C Write Action
    According to: 'Microchip: I2C_Over_USB_UserGuilde_50002283A.pdf' P.20
    """
    _USB2642I2CWRITESTREAM = 0x23

    """
    This Vendor Action marks an I2C Write-Read Action
    According to: 'Microchip: I2C_Over_USB_UserGuilde_50002283A.pdf' P.20
    """
    _USB2642I2CWRITEREADSTREAM = 0x22

    class _USB2642I2cWriteStruct(ctypes.Structure):
        """I2C-Write Data Structure for up to 512 Bytes of Data

        According to: 'Microchip: I2C_Over_USB_UserGuilde_50002283A.pdf' P.20
        """

        _fields_ = [
            ("ScsiVendorCommand", ctypes.c_uint8),
            ("ScsiVendorActionWriteI2C", ctypes.c_uint8),
            ("I2cSlaveAddress", ctypes.c_uint8),
            ("I2cUnused", ctypes.c_uint8),
            ("I2cDataPhaseLenHigh", ctypes.c_uint8),
            ("I2cDataPhaseLenLow", ctypes.c_uint8),
            ("I2cCommandPhaseLen", ctypes.c_uint8),
            ("I2cCommandPayload", ctypes.c_uint8 * 9),
        ]

    assert ctypes.sizeof(_USB2642I2cWriteStruct) == 16

    class _USB2642I2cReadStruct(ctypes.Structure):
        """
        I2C-Read Data Structure for up to 512 Bytes of Data.

        According to: 'Microchip: I2C_Over_USB_UserGuilde_50002283A.pdf' P.20
        """

        _fields_ = [
            ("ScsiVendorCommand", ctypes.c_uint8),
            ("ScsiVendorActionWriteReadI2C", ctypes.c_uint8),
            ("I2cWriteSlaveAddress", ctypes.c_uint8),
            ("I2cReadSlaveAddress", ctypes.c_uint8),
            ("I2cReadPhaseLenHigh", ctypes.c_uint8),
            ("I2cReadPhaseLenLow", ctypes.c_uint8),
            ("I2cWritePhaseLen", ctypes.c_uint8),
            ("I2cWritePayload", ctypes.c_uint8 * 9),
        ]

    assert ctypes.sizeof(_USB2642I2cReadStruct) == 16

    def _get_SCSI_cmd_I2C_write(self, slaveAddr, data):
        """
        Create an I2cWrite Command Structure to write up to 512 bytes to device
        slaveAddr.

        According to: 'Microchip: I2C_Over_USB_UserGuilde_50002283A.pdf' P.20
        """
        MAXLEN = 512
        count = min(len(data), MAXLEN)
        dataArray = (ctypes.c_uint8 * MAXLEN)()
        dataArray[:count] = data[:count]

        slaveWriteAddr = (slaveAddr * 2) & 0xFF

        cmd = self._USB2642I2cWriteStruct(
            ScsiVendorCommand=self._USB2642SCSIOPCODE,
            ScsiVendorActionWriteI2C=self._USB2642I2CWRITESTREAM,
            I2cSlaveAddress=slaveWriteAddr,
            I2cUnused=0x00,
            I2cDataPhaseLenHigh=(count >> 8) & 0xFF,
            I2cDataPhaseLenLow=count & 0xFF,
            I2cCommandPhaseLen=0x00,
            I2cCommandPayload=(ctypes.c_uint8 * 9)(),
        )

        return cmd, dataArray

    def _get_SCSI_cmd_I2C_write_read(self, slaveAddr, writeData, readLength):
        """
        Create an I2cWriteRead Command Structure to write up to 9 bytes to device
        slaveAddr and then read back up to 512 bytes of data.

        According to: 'Microchip: I2C_Over_USB_UserGuilde_50002283A.pdf' P.20
        """
        MAXLEN = 512
        readCount = min(readLength, MAXLEN)
        readDataArray = (ctypes.c_uint8 * MAXLEN)()

        MAXLEN = 9
        writeCount = min(len(writeData), MAXLEN)
        writeDataArray = (ctypes.c_uint8 * MAXLEN)()
        writeDataArray[:writeCount] = writeData[:writeCount]

        slaveWriteAddr = (slaveAddr * 2) & 0xFF
        slaveReadAddr = slaveWriteAddr + 1

        cmd = self._USB2642I2cReadStruct(
            ScsiVendorCommand=self._USB2642SCSIOPCODE,
            ScsiVendorActionWriteReadI2C=self._USB2642I2CWRITEREADSTREAM,
            I2cWriteSlaveAddress=slaveWriteAddr,
            I2cReadSlaveAddress=slaveReadAddr,
            I2cReadPhaseLenHigh=(readCount >> 8) & 0xFF,
            I2cReadPhaseLenLow=readCount & 0xFF,
            I2cWritePhaseLen=writeCount,
            I2cWritePayload=writeDataArray,
        )

        return cmd, readDataArray

    def write_config(self, data):
        """
        Writes the eeprom contents from data into the config EEPROM on the auxiliary
        I2C bus.

        This is done using reverse-engineered commands send by the Microchip
        Windows-Demo-Tool.

        Arguments:
        data -- EEPROM blob to write as ctype.buffer. Length 384 Bytes as described
                in the USB2642 Datasheet.
        """

        # SCSI Command was found on the USB-Bus.
        # Since most of the bytes are unknown this is used as plain magic.
        scsiCommand = list_to_uint8_array(
            [0xCF, 0x54, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], 16
        )

        # Data in the captured USB-transfer was suffixed with some random data.
        # Experiments showed that 0x00 works fine too.
        # Since the buffer is zero-ed when initialized the suffix could be removed.
        data_suffix = list_to_uint8_array([0x00], 127)

        # Copying prefix, data and suffix to the SCSI command data-section
        payload = (ctypes.c_uint8 * 512)()
        payload[: ctypes.sizeof(data)] = data
        payload[ctypes.sizeof(data) : ctypes.sizeof(data) + ctypes.sizeof(data_suffix)] = data_suffix  # noqa: E203

        # Perform the actual SCSI transfer
        _, status = execute_scsi_command(self.sg, scsiCommand, payload, "out")
        if status != 0:
            raise IoctlFailed(f"SCSI Transaction ended with status {status}. Config write failed.")

    def write_read_to(self, i2cAddr, writeData, readLength):
        """
        Tries to write data to an I2C-Device and afterwards read data from that
        device.

        This function will perform am I2C-Transaction like the following:

        * I2C-Start
        * I2C-Slave address with R/W = W (0)
        * writeData[0]
        * writeData[1]
        * ...
        * I2C-Repeated Start
        * I2C-Slave address with R/W = R (1)
        * readData[0]
        * readData[1]
        * ...
        * I2C-Stop

        This transaction can (for example) be used to set the address-pointer inside
        an EEPROM and read data from it.

        Arguments:
        i2cAddr -- 7-Bit I2C Slave address (as used by Linux). Will be shifted 1 Bit
                   to the left before adding the R/W-bit.
        writeData -- iterable of bytes to write in the first phase
        readLengh -- number of bytes (0..512) to read in the second phase
        """
        scsiCommand, data = self._get_SCSI_cmd_I2C_write_read(i2cAddr, writeData, readLength)
        # TODO: Add error handling if length of read or write do not match
        #       requirements

        #    print("I2C-Command:")
        #    print(self.to_pretty_hex(scsiCommand))
        #    print("I2C-Payload:")
        #    print(self.to_pretty_hex(data))
        data, status = execute_scsi_command(self.sg, scsiCommand, data, "in")

        if status != 0:
            raise I2cTransactionFailed(
                f"SCSI-Transaction ended with status {status}. I2C-Transaction has probably failed."
            )

        return list(data[:readLength])

    def write_to(self, i2cAddr, data):
        """
        Tries to write data to an I2C-Device.

        This function will perform am I2C-Transaction like the following:

        * I2C-Start
        * I2C-Slave address with R/W = W (0)
        * data[0]
        * data[1]
        * ...
        * I2C-Stop

        Transactions like this can (for example) be used if configuration registers
        on a device have to be written.

        Arguments:
        i2cAddr -- 7-Bit I2C Slave address (as used by Linux). Will be shifted 1 Bit
                   to the left before adding the R/W-bit.
        data -- iterateable of bytes to write."""
        scsiCommand, data = self._get_SCSI_cmd_I2C_write(i2cAddr, data)
        # TODO: Add length checks

        #    print("I2C-Command:")
        #    print(self.to_pretty_hex(scsiCommand))
        #    print("I2C-Payload:")
        #    print(self.to_pretty_hex(data))
        data, status = execute_scsi_command(self.sg, scsiCommand, data, "out")

        if status != 0:
            raise I2cTransactionFailed(
                f"SCSI-Transaction ended with status {status}. I2C-Transaction has probably failed."
            )

    def _read_register(self, reg, size, retries=5):
        scsiCommand = list_to_uint8_array(
            [0xCF, reg, 0x00, 0x00, size, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00], 16
        )

        while True:
            databuffer = ctypes.c_buffer(size)
            _, status = execute_scsi_command(self.sg, scsiCommand, databuffer, "in")

            if retries and status == 2:
                sleep(0.5)
                retries -= 1
                continue

            if status != 0:
                raise SDTransactionFailed(
                    f"SCSI Transaction ended with status {status}. SD Transaction has probably failed."
                )

            break

        return databuffer.raw

    def read_cid(self):
        return self._read_register(0x18, 16)

    def read_csd(self):
        return self._read_register(0x1A, 16)

    def read_scr(self):
        return self._read_register(0x1B, 8)
