#!/usr/bin/env python3

# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2025 The USB-SD-Mux Authors

"""
Platform-specific SCSI passthrough implementations.

This module exports platform-specific functions for SCSI operations.
The actual implementation depends on the operating system.
"""

import platform


# Exception definitions
class IoctlFailed(Exception):
    pass


if platform.system() == "Windows":
    # Windows SCSI implementation using DeviceIoControl
    import ctypes
    from ctypes import wintypes

    # Windows constants
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3
    FILE_SHARE_READ = 1
    FILE_SHARE_WRITE = 2
    INVALID_HANDLE_VALUE = -1
    IOCTL_SCSI_PASS_THROUGH_DIRECT = 0x4D014
    SCSI_IOCTL_DATA_OUT = 0
    SCSI_IOCTL_DATA_IN = 1
    SCSI_IOCTL_DATA_UNSPECIFIED = 2

    # Windows error codes
    ERROR_ACCESS_DENIED = 5
    ERROR_FILE_NOT_FOUND = 2
    ERROR_PATH_NOT_FOUND = 3

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class SCSI_PASS_THROUGH_DIRECT(ctypes.Structure):
        """Windows SCSI_PASS_THROUGH_DIRECT structure."""

        _fields_ = [
            ("Length", wintypes.USHORT),
            ("ScsiStatus", ctypes.c_ubyte),
            ("PathId", ctypes.c_ubyte),
            ("TargetId", ctypes.c_ubyte),
            ("Lun", ctypes.c_ubyte),
            ("CdbLength", ctypes.c_ubyte),
            ("SenseInfoLength", ctypes.c_ubyte),
            ("DataIn", ctypes.c_ubyte),
            ("DataTransferLength", wintypes.ULONG),
            ("TimeOutValue", wintypes.ULONG),
            ("DataBuffer", ctypes.c_void_p),
            ("SenseInfoOffset", wintypes.ULONG),
            ("Cdb", ctypes.c_ubyte * 16),
        ]

    class SCSI_PASS_THROUGH_DIRECT_WITH_SENSE(ctypes.Structure):
        """SCSI_PASS_THROUGH_DIRECT with sense buffer."""

        _fields_ = [
            ("sptd", SCSI_PASS_THROUGH_DIRECT),
            ("sense_buffer", ctypes.c_ubyte * 32),
        ]

    def execute_scsi_command(device_path, cdb, data_buffer, direction, timeout=5):
        """
        Execute a SCSI command on Windows using SCSI passthrough.

        Arguments:
        device_path -- Windows device path (e.g., r"\\\\.\\PhysicalDrive1")
        cdb -- Command Descriptor Block (ctypes structure or array)
        data_buffer -- ctypes array for data transfer (or None)
        direction -- 'in', 'out', or 'none'
        timeout -- Command timeout in seconds

        Returns:
        Tuple of (data_buffer, scsi_status)

        Raises:
        IoctlFailed: If the SCSI command fails
        """
        # Open device
        handle = kernel32.CreateFileW(
            device_path, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None
        )

        if handle == INVALID_HANDLE_VALUE:
            error = ctypes.get_last_error()
            if error == ERROR_ACCESS_DENIED:
                raise IoctlFailed(f"Access denied opening device '{device_path}'. Try running as Administrator.")
            elif error in (ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND):
                raise IoctlFailed(f"Device '{device_path}' not found. Check the device path in Device Manager.")
            else:
                raise IoctlFailed(f"Failed to open device '{device_path}'. Error code: {error}")

        try:
            # Map direction to Windows constants
            direction_map = {"in": SCSI_IOCTL_DATA_IN, "out": SCSI_IOCTL_DATA_OUT, "none": SCSI_IOCTL_DATA_UNSPECIFIED}
            data_direction = direction_map.get(direction)

            # Set up SCSI_PASS_THROUGH_DIRECT structure
            sptd_with_sense = SCSI_PASS_THROUGH_DIRECT_WITH_SENSE()
            ctypes.memset(ctypes.byref(sptd_with_sense), 0, ctypes.sizeof(sptd_with_sense))

            sptd = sptd_with_sense.sptd
            sptd.Length = ctypes.sizeof(SCSI_PASS_THROUGH_DIRECT)
            sptd.CdbLength = 16
            sptd.SenseInfoLength = 32
            sptd.DataIn = data_direction
            sptd.DataTransferLength = ctypes.sizeof(data_buffer) if data_buffer else 0
            sptd.TimeOutValue = timeout
            sptd.DataBuffer = ctypes.cast(data_buffer, ctypes.c_void_p) if data_buffer else None
            sptd.SenseInfoOffset = SCSI_PASS_THROUGH_DIRECT_WITH_SENSE.sense_buffer.offset

            # Copy CDB to SCSI structure
            ctypes.memmove(sptd.Cdb, ctypes.addressof(cdb), ctypes.sizeof(cdb))

            # Execute the SCSI command
            bytes_returned = wintypes.DWORD()

            success = kernel32.DeviceIoControl(
                handle,
                IOCTL_SCSI_PASS_THROUGH_DIRECT,
                ctypes.byref(sptd_with_sense),
                ctypes.sizeof(sptd_with_sense),
                ctypes.byref(sptd_with_sense),
                ctypes.sizeof(sptd_with_sense),
                ctypes.byref(bytes_returned),
                None,
            )

            if not success:
                error = ctypes.get_last_error()
                raise IoctlFailed(f"DeviceIoControl failed. Error code: {error}")

            return data_buffer, sptd.ScsiStatus
        finally:
            # Always close the device handle
            if handle != INVALID_HANDLE_VALUE:
                kernel32.CloseHandle(handle)

    def get_model(device_path):
        """
        Get SCSI model string using INQUIRY command on Windows.

        Arguments:
        device_path -- Windows device path (e.g., r"\\\\.\\PhysicalDrive1")

        Returns:
        Model string or None on failure
        """
        # Build INQUIRY CDB (6-byte command)
        cdb = (ctypes.c_ubyte * 16)()
        cdb[0] = 0x12  # INQUIRY opcode
        cdb[4] = 96  # Allocation length
        # Allocate data buffer for INQUIRY response
        data_buffer = (ctypes.c_ubyte * 96)()
        # Execute SCSI INQUIRY command
        _, status = execute_scsi_command(device_path, cdb, data_buffer, "in", timeout=5)
        if status != 0:
            return None
        # Parse INQUIRY response - product is at bytes 16-31
        data = bytes(data_buffer)
        product = data[16:32].decode("ascii", errors="ignore").strip().rstrip("\x00")
        return product


else:
    # Linux SCSI implementation using ioctl
    import ctypes
    import fcntl

    class _SgioHdrStruct(ctypes.Structure):
        """
        Structure used to access the ioctl() to send arbitrary SCSI-commands.

        Reflects the Kernel-Struct from:
        <scsi/sg.h> sg_io_hdr_t.
        """

        _fields_ = [
            ("interface_id", ctypes.c_int),
            ("dxfer_direction", ctypes.c_int),
            ("cmd_len", ctypes.c_ubyte),
            ("mx_sb_len", ctypes.c_ubyte),
            ("iovec_count", ctypes.c_ushort),
            ("dxfer_len", ctypes.c_uint),
            ("dxferp", ctypes.c_void_p),
            ("cmdp", ctypes.c_void_p),
            ("sbp", ctypes.c_void_p),
            ("timeout", ctypes.c_uint),
            ("flags", ctypes.c_uint),
            ("pack_id", ctypes.c_int),
            ("usr_ptr", ctypes.c_void_p),
            ("status", ctypes.c_ubyte),
            ("masked_status", ctypes.c_ubyte),
            ("msg_status", ctypes.c_ubyte),
            ("sb_len_wr", ctypes.c_ubyte),
            ("host_status", ctypes.c_ushort),
            ("driver_status", ctypes.c_ushort),
            ("resid", ctypes.c_int),
            ("duration", ctypes.c_uint),
            ("info", ctypes.c_uint),
        ]

    # sg_io_hdr_t contains 9 ints, 3 short ints, 6 chars and 4 pointers. So its
    # size is 9 * 4 + 3 * 2 + 6 * 1 + 4 * 4 = 64 on 32 bit architectures. On 64
    # bit architectures there are two holes in the struct:
    # - 4 bytes before *usr_ptr to make the pointer aligned
    # - 4 bytes at the end to make the size a multiple of 8.
    # So the size there is: 9 * 4 + 3 * 2 + 6 * 1 + 4 * 8 + 2 * 4 = 88.
    if ctypes.sizeof(ctypes.c_void_p) == 4:
        assert ctypes.sizeof(_SgioHdrStruct) == 64
    else:
        assert ctypes.sizeof(ctypes.c_void_p) == 8
        assert ctypes.sizeof(_SgioHdrStruct) == 88

    _SG_IO = 0x2285  # <scsi/sg.h>
    _SG_DXFER_NONE = -1
    _SG_DXFER_TO_DEV = -2
    _SG_DXFER_FROM_DEV = -3

    def execute_scsi_command(device_path, cdb, data_buffer, direction, timeout=5):
        """
        Execute a SCSI command on Linux using ioctl.

        Arguments:
        device_path -- Linux device path (e.g., "/dev/sg1")
        cdb -- Command Descriptor Block (ctypes structure or array)
        data_buffer -- ctypes buffer/array for data transfer
        direction -- 'in', 'out', or 'none'
        timeout -- Command timeout in seconds

        Returns:
        Tuple of (data_buffer, scsi_status)

        Raises:
        IoctlFailed: If the SCSI command fails
        """
        # Map direction to Linux constants
        direction_map = {"in": _SG_DXFER_FROM_DEV, "out": _SG_DXFER_TO_DEV, "none": _SG_DXFER_NONE}
        sg_dxfer = direction_map.get(direction, _SG_DXFER_NONE)

        # Create sense buffer
        sense = ctypes.c_buffer(64)

        # Build SGIO structure
        sgio = _SgioHdrStruct(
            interface_id=ord("S"),
            dxfer_direction=sg_dxfer,
            cmd_len=ctypes.sizeof(cdb),
            mx_sb_len=ctypes.sizeof(sense),
            iovec_count=0,
            dxfer_len=ctypes.sizeof(data_buffer) if data_buffer else 0,
            dxferp=ctypes.cast(data_buffer, ctypes.c_void_p) if data_buffer else None,
            cmdp=ctypes.cast(ctypes.addressof(cdb), ctypes.c_void_p),
            sbp=ctypes.cast(sense, ctypes.c_void_p),
            timeout=timeout * 1000,  # Convert to milliseconds
            flags=0,
            pack_id=0,
            usr_ptr=None,
            status=0,
            masked_status=0,
            msg_status=0,
            sb_len_wr=0,
            host_status=0,
            driver_status=0,
            resid=0,
            duration=0,
            info=0,
        )

        # Execute ioctl
        with open(device_path, "r+b", buffering=0) as fh:
            rc = fcntl.ioctl(fh, _SG_IO, sgio)
            if rc != 0:
                raise IoctlFailed(f"SG_IO ioctl() failed with non-zero exit-code {rc}")

        return data_buffer, sgio.status

    def get_model(device_path):
        """
        Get SCSI model string from sysfs on Linux.

        Arguments:
        device_path -- Linux device path (e.g., "/dev/sg1")

        Returns:
        Model string or None on failure
        """
        import os

        try:
            # Resolve symlink and get sg device name
            base_sg = os.path.realpath(device_path)
            sg_name = os.path.basename(base_sg)

            # Read model from sysfs
            model_filename = f"/sys/class/scsi_generic/{sg_name}/device/model"
            with open(model_filename) as fh:
                model = fh.read().strip()

            return model
        except (FileNotFoundError, OSError):
            return None
