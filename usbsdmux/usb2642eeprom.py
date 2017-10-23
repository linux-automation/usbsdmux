#!/usr/bin/env python3

import struct
import ctypes
from .usb2642i2c import Usb2642I2C
import time
import argparse
import sys
from .ctypehelper import string_to_microchip_unicode_uint8_array,\
  string_to_uint8_array, list_to_uint8_array, to_pretty_hex


"""
This module provides the high-level interface needed to write the contents of
the configuration-EEPROM of a USB2642 using the USB2642.
"""


class VerificationFailedException(Exception):
  pass


class USB2642Eeprom(object):
  """
  Provides an interface to write the configuration EEPROM of a USB2642.
  """

  def __init__(self, sg, i2c_addr=0x50):
    """"
    Create a new USB2642Eeprom Instance.

    Arguments:
    sg -- /dev/sg* to use
    i2c_addr -- 7-Bit Address of the EEPROM to use. Defaults to 0x50 for the
                configuration-EEPROM. You probably do NOT want to override this.
    """

    self.i2c = Usb2642I2C(sg)
    self.addr = i2c_addr

  class _EepromStruct(ctypes.Structure):
    """
    Struct that contains the Configuration of the Card Reader and USB Hub.
    """
    _pack_ = 1 # forces the struct to be packed tight and overrides the default
               # 4-byte aligned packing.
    _fields_ = [

      # Flash Media Controller Configuration
      ('USB_SER_NUM', ctypes.c_uint8*(0x19-0x00+1)),    # 0x00  .. 0x19  USB Serial Number
      ('USB_VID', ctypes.c_uint16),                     # 0x1A  .. 0x1B  USB Vendor ID
      ('USB_PID', ctypes.c_uint16),                     # 0x1C  .. 0x1D  USB Product ID
      ('USB_LANG_ID', ctypes.c_uint8*(0x21-0x1E+1)),    # 0x1E  .. 0x21  USB Language Identifier, see http://www.usb.org/developers/docs/USB_LANGIDs.pdf
      ('USB_MFR_STR', ctypes.c_uint8*(0x5D-0x22+1)),    # 0x22  .. 0x5D  USB Manufacturer String (Unicode)
      ('USB_PRD_STR', ctypes.c_uint8*(0x99-0x5E+1)),    # 0x5E  .. 0x99  USB Product String (Unicode)
      ('USB_BM_ATT', ctypes.c_uint8),                   # 0x9A           USB BmAttribute, see http://sdphca.ucsd.edu/lab_equip_manuals/usb_20.pdf, P.266
      ('USB_MAX_PWR', ctypes.c_uint8),                  # 0x9B           USB Max Power, see http://sdphca.ucsd.edu/lab_equip_manuals/usb_20.pdf, P.266, 1 Digit = 2mA
      ('ATT_LB', ctypes.c_uint8),                       # 0x9C           Attribute Lo byte
      ('ATT_HLB', ctypes.c_uint8),                      # 0x9D           Attribute Hi Lo byte
      ('ATT_LHB', ctypes.c_uint8),                      # 0x9E           Attribute Lo Hi byte
      ('ATT_HB', ctypes.c_uint8),                       # 0x9F           Attribute Hi byte
      ('reserved0', ctypes.c_uint8*(0xA4-0xA0)),        # 0xA0  .. 0xA3  reserved
      ('LUN_PWR_LB', ctypes.c_uint8),                   # 0xA4           LUN Power Lo byte
      ('LUN_PWR_HB', ctypes.c_uint8),                   # 0xA5           LUN Power Hi byte
      ('reserved1', ctypes.c_uint8*(0xBF-0xA6)),        # 0xA6  .. 0xBE  reserved
      ('DEV3_ID_STR', ctypes.c_uint8*(0xC6-0xBF)),      # 0xBF  .. 0xC5  Card Reader Identifyer String
      ('INQ_VEN_STR', ctypes.c_uint8*(0xCE-0xC6)),      # 0xC6  .. 0xCD  Inquiry Vendor String
      ('INQ_PRD_STR', ctypes.c_uint8*(0xD3-0xCE)),      # 0xCE  .. 0xD2  48QFN Inquiry Product String
      ('DYN_NUM_LUN', ctypes.c_uint8),                  # 0xD3           Dynamic Number of LUNs
      ('LUN_DEV_MAP', ctypes.c_uint8*(0xD8-0xD4)),      # 0xD4  .. 0xD7  LUN to Device Mapping
      ('reserved2', ctypes.c_uint8*(0xDB-0xD8)),        # 0xD8  .. 0xDA  reserved

      # HUB CONTROLLER CONFIGURATION
      ('SD_MMC_BUS_TIMING', ctypes.c_uint8*(0xDE-0xDB)),# 0xDB  .. 0xDD  SD/MMC Bus Timing Control
      ('VID', ctypes.c_uint16),                         # 0xDE  .. 0xDF  Hub Vendor ID
      ('PID', ctypes.c_uint16),                         # 0xE0  .. 0xE1  Hub Product ID
      ('DID', ctypes.c_uint16),                         # 0xE2  .. 0xE3  Hub Device ID
      ('CFG_DAT_BYTE1', ctypes.c_uint8),                # 0xE4           Configuration Data Byte 1
      ('CFG_DAT_BYTE2', ctypes.c_uint8),                # 0xE5           Configuration Data Byte 2
      ('CFG_DAT_BYTE3', ctypes.c_uint8),                # 0xE6           Configuration Data Byte 3
      ('NR_DEVICE', ctypes.c_uint8),                    # 0xE7           Non-Removeable Devices
      ('PORT_DIS_SP', ctypes.c_uint8),                  # 0xE8           Port Disable (Self)
      ('PORT_DIS_BP', ctypes.c_uint8),                  # 0xE9           Post Disable (Bus)
      ('MAX_PWR_SP', ctypes.c_uint8),                   # 0xEA           Max Power (Self)
      ('MAX_PWR_BP', ctypes.c_uint8),                   # 0xEB           Max Power (Bus)
      ('HC_MAX_C_SP', ctypes.c_uint8),                  # 0xEC           Hub Controller Max Current (Self)
      ('HC_MAX_C_BP', ctypes.c_uint8),                  # 0xED           Hub Controller Max Current (Bus)
      ('PWR_ON_TIME', ctypes.c_uint8),                  # 0xEE           Power-on time
      ('BOOST_UP', ctypes.c_uint8),                     # 0xEF           Boost_Up
      ('BOOST_32', ctypes.c_uint8),                     # 0xF0           Boost_3:2
      ('PRT_SWP', ctypes.c_uint8),                      # 0xF1           Port Swap
      ('PRTM12', ctypes.c_uint8),                       # 0xF2           Port Map 12
      ('PRTM3', ctypes.c_uint8),                        # 0xF3           Port Map 3

      # OTHER CONFIGURATION
      ('SD_CLK_LIM', ctypes.c_uint8),                   # 0xF4           SD Clock Limit for the Flash Media Controller
      ('reserved3', ctypes.c_uint8),                    # 0xF5           reserved
      ('MEDIA_SETTINGS', ctypes.c_uint8),               # 0xF6           SD1 Timeout Configuration
      ('reserved4', ctypes.c_uint8*(0xFC-0xF7)),        # 0xF7  .. 0xFB  reserved
      ('NVSTORE_SIG', ctypes.c_uint8*(0xFF-0xFC+1)),    # 0xFC  .. 0xFF  Non-Volatile Storage Signature

      # Non Volatile Storage 2 Contents
      ('CLUN0_ID_STR', ctypes.c_uint8*(0x106-0x100+1)), # 0x100 .. 0x106 LUN 0 Identifier String
      ('CLUN1_ID_STR', ctypes.c_uint8*(0x10D-0x107+1)), # 0x107 .. 0x10D LUN 1 Identifier String
      ('CLUN2_ID_STR', ctypes.c_uint8*(0x114-0x10E+1)), # 0x10E .. 0x114 LUN 2 Identifier String
      ('CLUN3_ID_STR', ctypes.c_uint8*(0x11B-0x115+1)), # 0x115 .. 0x11B LUN 3 Identifier String
      ('CLUN4_ID_STR', ctypes.c_uint8*(0x122-0x11C+1)), # 0x11C .. 0x122 LUN 4 Identifier String
      ('reserved5', ctypes.c_uint8*(0x145-0x123+1)),    # 0x123 .. 0x145 reserved
      ('DYN_NUM_EXT_LUN', ctypes.c_uint8),              # 0x146          Dynamic Number of Extended LUNs
      ('LUN_DEV_MAP2', ctypes.c_uint8*(0x14B-0x147+1)),  # 0x147 .. 0x14B LUN to Device mapping
      ('reserved6', ctypes.c_uint8*(0x17B-0x14C+1)),    # 0x14C .. 0x17B reserved
      ('NVSTORE_SIG2', ctypes.c_uint8*(0x17F-0x17C+1))  # 0x17C .. 0x17F Non-Volatile Storage 2 Signature
      ]

    def get_struct(reader_VID, reader_PID, reader_vendorString,\
                   reader_productString, reader_serial, scsi_mfg, scsi_product):
      """
      Returns a pre-filled EepromStruct.

      Parameters are taken from the Datasheets defaults if nothing else is
      mentioned.
      """
      s = USB2642Eeprom._EepromStruct(
        USB_SER_NUM = string_to_microchip_unicode_uint8_array(reader_serial, 0x19-0x00+1),
        USB_VID = 0x0424,
        USB_PID = 0x4041,
        USB_LANG_ID = list_to_uint8_array([0x04, 0x03, 0x09, 0x04], 0x21-0x1E+1), # reverse engineered from actual EEPROM. Does NOT match the datasheet.
        USB_MFR_STR = string_to_microchip_unicode_uint8_array(reader_vendorString, 0x5D-0x22+1),
        USB_PRD_STR = string_to_microchip_unicode_uint8_array(reader_productString, 0x99-0x5E+1),
        USB_BM_ATT = 0x80, # Bus Powered, without Remote wakeup
        USB_MAX_PWR = 0x30,# 0x30 * 2mA = 96mA Power Consumption
        ATT_LB = 0x50, # use INQ-strings, SD card is write protected when SW_nWP is high
        ATT_HLB = 0x80,
        ATT_LHB = 0x00,
        ATT_HB = 0x00,
        LUN_PWR_LB = 0x00,
        LUN_PWR_HB = 0x0A,
        DEV3_ID_STR = string_to_uint8_array("SD/MMC", 0xC5-0xBF+1, encoding="UTF-8", padding=0x00),
        INQ_VEN_STR = string_to_uint8_array(scsi_mfg, 0xCD-0xC6+1, encoding="UTF-8", padding=0x00),
        INQ_PRD_STR = string_to_uint8_array(scsi_product, 0xD2-0xCE+1, encoding="UTF-8", padding=0x00),
        DYN_NUM_LUN = 0x01,
        LUN_DEV_MAP = list_to_uint8_array([0xFF, 0x00, 0x00, 0x00], 0xD7-0xD4+1),
        SD_MMC_BUS_TIMING = list_to_uint8_array([0x59, 0x56, 0x97], 0xDD-0xDB+1),
        VID = 0x0424,
        PID = 0x2640,
        DID = 0x08A2,
        CFG_DAT_BYTE1 = 0x8B,
        CFG_DAT_BYTE2 = 0x28,
        CFG_DAT_BYTE3 = 0x00,
        NR_DEVICE = 0x02,
        PORT_DIS_SP = 0x0C, # Disable the unused Downstream-Ports of the hub
        PORT_DIS_BP = 0x0C, # Disable the unused Downstream-Ports of the hub
        MAX_PWR_SP = 0x01,
        MAX_PWR_BP = 0x32,
        HC_MAX_C_SP = 0x01,
        HC_MAX_C_BP = 0x32,
        PWR_ON_TIME = 0x32,
        BOOST_UP = 0x00,
        BOOST_32 = 0x00,
        PORT_SWP = 0x00,
        PRTM12 = 0x00,
        PRTM3 = 0x00,
        SD_CLK_LIM = 0x00,
        MEDIA_SETTINGS = 0x00,
        NVSTORE_SIG = string_to_uint8_array("ata2", 4, c_string=False, encoding="UTF-8"),
        # according to datasheet the signature is "ATA2".
        # But reverse engineering the configuration written with the microchip-tool shows that it should be "ata" instead.
        CLUN0_ID_STR = string_to_uint8_array("COMBO", 0x106-0x100+1, encoding="UTF-8", padding=0x00),
        CLUN1_ID_STR = string_to_uint8_array("COMBO", 0x106-0x100+1, encoding="UTF-8", padding=0x00),
        CLUN2_ID_STR = string_to_uint8_array("COMBO", 0x106-0x100+1, encoding="UTF-8", padding=0x00),
        CLUN3_ID_STR = string_to_uint8_array("COMBO", 0x106-0x100+1, encoding="UTF-8", padding=0x00),
        CLUN4_ID_STR = string_to_uint8_array("COMBO", 0x106-0x100+1, encoding="UTF-8", padding=0x00),
        DYN_NUM_EXT_LUN = 0x00,
        LUN_DEV_MAP2 = list_to_uint8_array([0xFF, 0xFF, 0xFF, 0xFF], 0x14B-0x147+1),
        NVSTORE_SIG2 = string_to_uint8_array("ecf1", 0x17F-0x17C+1, encoding="UTF-8", padding=0x00)
      )
      assert ctypes.sizeof(s) == 384
      return s


  def _read_EEPROM(self, addr=0, len=256):
    """
    Reads len bytes of data starting from addr from the given EEPROM.

    Attributes:
    addr -- Byte address from where to start reading
    len  -- Number of bytes to read (0..256)
    """

    return self.i2c.write_read_to(self.addr, [addr], len)

  def _write_EEPROM(self, addr, data):
    """
    Writes data to the EEPROM starting at addr.

    Attributes:
    addr -- Address to begin write at
    data -- Iterable containing data to write
    """

    offset=0
    while offset < len(data):
      #determine minimum and maximum address to write in this block
      lower = max((addr+offset)&0xF0, addr)
      upper = min(((addr+offset)&0xF0) | 0x0F, addr + len(data))

      lowerOffset = lower-addr
      upperOffset = upper-addr

      self.i2c.write_to(self.addr, [lower]+data[lowerOffset:(upperOffset+1)])
      time.sleep(0.1)
      offset = upperOffset+1

  def write(self, VID, PID, product_string, vendor_string, serial, scsi_mfg,\
            scsi_product):
    """
    Writes a configuration to the EEPROM.

    Arguments:
    VID -- USB Vendor ID, uint_16
    PID -- USB Product ID, uint_16
    product_string -- Product Name as String
    vendor_string -- Vendor Name as String
    serial -- Serial Number, 12 Hex Digits
    """

    s = USB2642Eeprom._EepromStruct.get_struct(
      reader_VID=VID,
      reader_PID=PID,
      reader_productString=product_string,
      reader_vendorString=vendor_string,
      reader_serial = serial,
      scsi_mfg = scsi_mfg,
      scsi_product = scsi_product
    )
    buffer = (ctypes.c_uint8*ctypes.sizeof(s))()
    ctypes.memmove(ctypes.addressof(buffer), ctypes.addressof(s),\
                   ctypes.sizeof(s))

    self.i2c.write_config(buffer)

def main():
  parser = argparse.ArgumentParser(description=\
             "This tool writes and verifies the configuration EEPROM of the usb-sd-mux with the information given on the command line.")
  parser.add_argument("sg",\
                      help="The /dev/sg* which is used.")
  parser.add_argument("--productString",\
                      help="Sets the product name that will be written.",\
                      default="usb-sd-mux_rev1")
  parser.add_argument("--manufacturerString",\
                      help="Sets the manufacturerString that will be written.",\
                      default="Pengutronix")
  parser.add_argument("--VID",\
                      help="Sets the VID that will be written.",\
                      default="0x0424")
  parser.add_argument("--ScsiManufacturer",\
                      help="Sets the ScsiManufacturer that will be written.",\
                      default="PTX")
  parser.add_argument("--ScsiProduct",\
                      help="Sets the ScsiProduct that will be written.",\
                      default="sdmux")
  parser.add_argument("--PID",\
                      help="Sets the USB-PIC that will be written.",\
                      default="0x4041")
  parser.add_argument("serial",\
                      help="Sets the Serial Number that will be written.")

  args = parser.parse_args()

  c = USB2642Eeprom(args.sg)

  c.write(
    VID=int(args.VID, base=16),
    PID=int(args.PID, base=16),
    product_string=args.productString,
    vendor_string=args.manufacturerString,
    serial = args.serial,
    scsi_mfg = args.ScsiManufacturer,
    scsi_product = args.ScsiProduct
  )

  print("Write completed")


if __name__ == "__main__":
  main()
