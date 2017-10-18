#!/usr/bin/env python3

import ctypes
import string
"""
This module contains functions related to packing data into ctype arrays in
special ways as needed by the Microchip USB2642.
"""


def string_to_uint8_array(str,
                          array_length,
                          c_string=False,
                          padding=0xFF,
                          encoding="UTF-16"):
    """
  Converts a python-string into a ctypes.c_uint8 array of a given length.
    The str will be encoded with the given encoding before converting.

  If c_string is True the string will be terminated with 0x00.
  str will be padded with padding if the buffer is longer than the str.
  str will be cropped if the buffer is shorter.

  Arguments:
  str -- python string
  array_length -- length of the resulting array in bytes.
  c_string -- Switch to treat a str as c-string. String will be terminated with 0x00
  padding -- This value will be used to pad buffer to the given length.
  """

    # Preparing output array
    byte_buf = (ctypes.c_uint8 * array_length)()
    for i in range(array_length):
        byte_buf[i] = padding

    # Determine number of bytes to copy
    nbytes = str.encode(encoding)
    if c_string:
        count = min(len(nbytes), array_length - 1)
    else:
        count = min(len(nbytes), array_length)

    # Do the actual copy
    for i in range(count):
        byte_buf[i] = int(nbytes[i])

    # Make string a c-string
    if c_string:
        i += 1
        byte_buf[i] = 0x00

    return byte_buf


def string_to_microchip_unicode_uint8_array(text, array_length, constant=0x03):
    """
  Converts a String to a USB2642 UTF-16 string.

  The USB2642 requires the first two bytes of the string to be
  <length including first two bytes><0x03>.
  This function first creates a UTF-16 string and then replaces the byte-order
  mark with this information.

  Arguments:
  text -- Text to copy into the array
  constant -- The constant byte placed into the 2nd byte
  """

    byte_buf = string_to_uint8_array(text, array_length)
    byte_buf[0] = len(text) * 2 + 2
    byte_buf[1] = constant
    return byte_buf


def list_to_uint8_array(numbers, array_length):
    """
  Converts a list of numbers into a ctypes.c_uint8 array of a given length.

  If numbers is too short for array_length it will be padded with 0x00.
  If numbers is too long it will be cropped.

  Arguments:
  numbers -- iterable of numbers (int, bytes, float...)
  array_length -- length of the resulting array
  """

    byte_buf = (ctypes.c_uint8 * array_length)()

    count = min(len(numbers), array_length)
    for i in range(count):
        byte_buf[i] = int(numbers[i])
    return byte_buf


def to_pretty_hex(buffer):
    """Takes a byte-buffer and creates a pretty-looking hex-string from it"""

    if isinstance(buffer, ctypes.Structure):
        out = ctypes.create_string_buffer(ctypes.sizeof(buffer))
        ctypes.memmove(
            ctypes.addressof(out),
            ctypes.addressof(buffer), ctypes.sizeof(buffer))
        temp_buf = [ord(x) for x in out]
    elif isinstance(buffer[0], int):
        temp_buf = [x for x in buffer]
    else:
        temp_buf = [ord(x) for x in buffer]

    res = ""
    offs = 0
    while len(temp_buf) > 0:
        window = temp_buf[0:8]
        temp_buf = temp_buf[8:]
        res += "0x{:02X}\t{}  {}\n".format(offs, " ".join(
            ["{:02X}".format(x) for x in window]), " ".join([
                chr(x) if chr(x) in string.printable.split(" ")[0] else "."
                for x in window
            ]))
        offs += 8
    return res
