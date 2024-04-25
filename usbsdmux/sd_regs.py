#!/usr/bin/env python3

# SPDX-License-Identifier: LGPL-2.1-or-later

# Copyright (C) 2023 Pengutronix, Jan Lübbe <entwicklung@pengutronix.de>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA


def bitslice(val, upper, lower):
    "extract a contiguous slice of bits from a larger value"
    size = upper - lower + 1
    mask = (1 << size) - 1
    return (val >> lower) & mask


def decoded_to_text(decoded):
    "convert the output of the decode() function to human-readable text"
    text = []
    text.append(f"{decoded['reg']} Register Value: {decoded['raw']}")
    for f in decoded["fields"]:
        if "name" in f:
            text.append(f"  {f['field']}: {f['name']}")
        else:
            text.append(f"  {f['field']}")
        raw = f["raw"]
        text.append(f"    raw: 0b{format(raw[0], '0%db' % raw[1])} == 0x{raw[0]:0x} == {int(raw[0])}")
        if "enum" in f:
            text.append(f"    enum: {f['enum']} {f.get('unit', '')}".rstrip())
        if "bits" in f:
            text.append(f"    bits: {', '.join(f['bits'])}")
        if "decoded" in f:
            text.append(f"    decoded: {f['decoded']}")
        if "value" in f:
            text.append(f"    value: {f['value']} {f.get('unit', '')}".rstrip())
    return text


class RegisterDecoder:
    "decode a register based on a mostly declarative description of the contents."

    FIELDS = {}

    def __init__(self, raw_hex):
        self.raw_hex = raw_hex
        self.raw = int(raw_hex, 16)

    def _get_slice(self, field):
        field = self.FIELDS[field]
        return field["slice"]

    def _get_details(self, field):
        field = self.FIELDS[field]
        return field

    def _get_value(self, field):
        upper, lower = self._get_slice(field)
        width = upper - lower + 1
        value = bitslice(self.raw, upper, lower)
        return (value, width)

    def __getattr__(self, field):
        v, _ = self._get_value(field)
        details = self._get_details(field)
        if "convert" in details:
            v = details["convert"](v)
        return v

    def decode_field(self, field):
        "decode a single field into a key-value format"
        result = {}

        value, width = self._get_value(field)
        details = self._get_details(field)
        result["field"] = field
        if "name" in details:
            result["name"] = details["name"]
        result["raw"] = (value, width)
        if "enum" in details:
            try:
                result["enum"] = details["enum"][value]
            except (IndexError, KeyError):
                result["enum"] = None
        if "bits" in details:
            bits = [details["bits"][x] for x in range(width) if (value & (1 << x))]
            result["bits"] = bits
        if "convert" in details:
            result["value"] = str(details["convert"](value))
        if "unit" in details:
            result["unit"] = details["unit"]
        if "decode" in details:
            decoded = details["decode"](self)
            result.update(decoded)

        return result

    def get_computed(self):
        "compute additional values which need multiple fields as input"
        return {}

    def decode(self):
        "decode all fields into a format suitable for JSON encoding"
        result = {"reg": self.__class__.__name__, "raw": self.raw_hex, "fields": []}

        for field, _ in sorted(self.FIELDS.items(), key=lambda x: x[1]["slice"], reverse=True):
            result["fields"].append(self.decode_field(field))
        result["computed"] = self.get_computed()

        return result

    def get_text_report(self):
        "decode all fields and format as human-readable text"
        decoded = self.decode()
        return decoded_to_text(decoded)


class CSD_Common(RegisterDecoder):
    TIME_VALUE_ENUM = ["reserved", 1.0, 1.2, 1.3, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0]

    def decode_TAAC(self):
        v = self._get_value("TAAC")
        TIME_UNIT_ENUM = ["1ns", "10ns", "100ns", "1us", "10us", "100us", "1ms", "10ms"]
        TIME_SCALE_ENUM = [1, 10, 100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000]
        unit = TIME_UNIT_ENUM[bitslice(v[0], 2, 0)]
        scale = TIME_SCALE_ENUM[bitslice(v[0], 2, 0)]
        value = self.TIME_VALUE_ENUM[bitslice(v[0], 6, 3)]

        scaled_value = value * scale if isinstance(value, float) else None

        return {
            "decoded": (value, unit),
            "value": scaled_value,
            "unit": "ns",
        }

    def decode_TRAN_SPEED(self):
        v = self._get_value("TRAN_SPEED")
        RATE_UNIT_ENUM = ["100 Kbit/s", "1Mbit/s", "10Mbit/s", "100Mbit/s", "reserved"]
        RATE_SCALE_ENUM = [100_000, 1_000_000, 10_000_000, 10_000_000, "reserved"]
        unit = RATE_UNIT_ENUM[bitslice(v[0], 2, 0)]
        scale = RATE_SCALE_ENUM[bitslice(v[0], 2, 0)]
        value = self.TIME_VALUE_ENUM[bitslice(v[0], 6, 3)]

        scaled_value = None

        if isinstance(value, float) and isinstance(scale, int):
            scaled_value = value * scale

        return {
            "decoded": (value, unit),
            "value": scaled_value,
            "unit": "bit/s",
        }

    FIELDS = {
        "CSD_STRUCTURE": {
            "slice": (127, 126),
            "name": "CSD structure",
            "enum": ["1.0", "2.0"],
        },
        "TAAC": {
            "slice": (119, 112),
            "name": "data read access-time-1",
            "decode": decode_TAAC,
        },
        "NSAC": {
            "slice": (111, 104),
            "name": "data read access-time-2",
            "convert": lambda v: v * 100,
            "unit": "CLK cycles",
        },
        "TRAN_SPEED": {
            "slice": (103, 96),
            "name": "max. data transfer rate",
            "decode": decode_TRAN_SPEED,
        },
        "CCC": {"slice": (95, 84), "name": "card command classes", "bits": [str(x) for x in range(12)]},
        "READ_BL_LEN": {
            "slice": (83, 80),
            "name": "max. read data block length",
            "convert": lambda v: 2**v,
            "unit": "bytes",
        },
        "READ_BL_PARTIAL": {
            "slice": (79, 79),
            "name": "partial blocks for read allowed",
            "convert": bool,
        },
        "WRITE_BLK_MISALIGN": {
            "slice": (78, 78),
            "name": "write block misalignment allowed",
            "convert": bool,
        },
        "READ_BLK_MISALIGN": {
            "slice": (77, 77),
            "name": "read block misalignment allowed",
            "convert": bool,
        },
        "DSR_IMP": {
            "slice": (76, 76),
            "name": "driver stage register implemented",
            "convert": bool,
        },
        "ERASE_BLK_EN": {
            "slice": (46, 46),
            "name": "erase single block enable",
            "convert": bool,
        },
        "SECTOR_SIZE": {
            "slice": (45, 39),
            "name": "erase sector size",
            "convert": lambda v: v + 1,
            "unit": "write blocks",
        },
        "WP_GRP_SIZE": {
            "slice": (38, 32),
            "name": "write protect group size",
            "convert": lambda v: v + 1,
            "unit": "erase sectors",
        },
        "WP_GRP_ENABLE": {
            "slice": (31, 31),
            "name": "write protect group enable",
            "convert": bool,
        },
        "R2W_FACTOR": {
            "slice": (28, 26),
            "name": "write speed factor",
            "convert": lambda v: 2**v,
            "unit": "multiples of read access time",
        },
        "WRITE_BL_LEN": {
            "slice": (25, 22),
            "name": "max. write data block length",
            "convert": lambda v: 2**v,
            "unit": "bytes",
        },
        "WRITE_BL_PARTIAL": {
            "slice": (21, 21),
            "name": "partial blocks for write allowed",
            "convert": bool,
        },
        "FILE_FORMAT_GRP": {
            "slice": (15, 15),
            "name": "file format group",
        },
        "COPY": {
            "slice": (14, 14),
            "name": "copy flag",
            "convert": bool,
        },
        "PERM_WRITE_PROTECT": {
            "slice": (13, 13),
            "name": "permanent write protection",
            "convert": bool,
        },
        "TMP_WRITE_PROTECT": {
            "slice": (12, 12),
            "name": "temporary write protection",
            "convert": bool,
        },
        "FILE_FORMAT": {
            "slice": (11, 9),
            "name": "file format",
            "enum": [
                "Hard disk-like file system with partition table",
                "DOS FAT (floppy-like) with boot sector only (no partition table)",
                "Universal File Format",
                "Others/Unknown",
            ],
        },
        "CRC": {
            "slice": (7, 1),
        },
    }

    def get_computed(self):
        result = {}

        sector_size = self.SECTOR_SIZE * self.WRITE_BL_LEN
        wp_grp_size = self.WP_GRP_SIZE * sector_size

        result["sector_size_bytes"] = {
            "value": sector_size,
            "unit": "bytes",
            "name": "sector size",
        }
        result["wp_grp_size_bytes"] = {
            "value": wp_grp_size,
            "unit": "bytes",
            "name": "write protect group size",
        }

        return result


class CSD_10(CSD_Common):
    VDD_MIN_CURR_MA_ENUM = [0.5, 1, 5, 10, 25, 35, 60, 100]
    VDD_MAX_CURR_MA_ENUM = [1, 5, 10, 25, 35, 45, 80, 200]

    FIELDS = CSD_Common.FIELDS.copy()
    FIELDS["C_SIZE"] = {
        "slice": (73, 62),
        "name": "device size",
        "convert": lambda v: (v + 1),
    }
    FIELDS["VDD_R_CURR_MIN"] = {
        "slice": (61, 59),
        "name": "max. read current @VDD min",
        "enum": VDD_MIN_CURR_MA_ENUM,
        "unit": "mA",
    }
    FIELDS["VDD_R_CURR_MAX"] = {
        "slice": (58, 56),
        "name": "max. read current @VDD max",
        "enum": VDD_MAX_CURR_MA_ENUM,
        "unit": "mA",
    }
    FIELDS["VDD_W_CURR_MIN"] = {
        "slice": (55, 53),
        "name": "max. write current @VDD min",
        "enum": VDD_MIN_CURR_MA_ENUM,
        "unit": "mA",
    }
    FIELDS["VDD_W_CURR_MAX"] = {
        "slice": (52, 50),
        "name": "max. write current @VDD max",
        "enum": VDD_MAX_CURR_MA_ENUM,
        "unit": "mA",
    }
    FIELDS["C_SIZE_MULT"] = {"slice": (49, 47), "name": "device size multiplier", "convert": lambda v: 2 ** (v + 2)}

    def get_computed(self):
        result = super().get_computed()

        device_size = self.C_SIZE * self.C_SIZE_MULT * self.READ_BL_LEN

        result["device_size_bytes"] = {
            "value": device_size,
            "unit": "bytes",
            "name": "device size",
        }

        return result


class CSD_20(CSD_Common):
    FIELDS = CSD_Common.FIELDS.copy()
    FIELDS["C_SIZE"] = {
        "slice": (69, 48),
        "name": "device size",
        "convert": lambda v: (v + 1) * 512 * 1024,
        "unit": "bytes",
    }


def decode_csd(raw_hex):
    raw = int(raw_hex, 16)
    val = bitslice(raw, 127, 126)
    if val == 0:
        return CSD_10(raw_hex)
    elif val == 1:
        return CSD_20(raw_hex)
    else:
        raise ValueError(f"unknown CSD version {val}")


class CID(RegisterDecoder):
    @staticmethod
    def convert_printable(value, size):
        # The spec defines some fields as ASCII strings, but in practice, cards
        # contain many other values as well. Clean up non-printable characters,
        # newlines, etc.
        result = ""
        for i in reversed(range(size)):
            c = chr((value >> 8 * i) & 0x7F)
            result += c if c.isprintable() else "."
        return result

    FIELDS = {
        "MID": {
            "slice": (127, 120),
            "name": "Manufacturer ID",
            "enum": {
                0x02: "SanDisk",
                0x03: "SanDisk SD",
                0x1B: "Samsung",
                0x74: "Transcend",
                0x9F: "Kingston SD",
            },
        },
        "OID": {
            "slice": (119, 104),
            "name": "OEM/Application ID",
            "convert": lambda v: CID.convert_printable(v, 2),
        },
        "PNM": {
            "slice": (103, 64),
            "name": "Product name",
            "convert": lambda v: CID.convert_printable(v, 5),
        },
        "PRV": {
            "slice": (63, 56),
            "name": "Product revision",
            "convert": lambda v: f"{int(v >> 4 & 15)}.{int(v & 15)}",
        },
        "PSN": {
            "slice": (55, 24),
            "name": "Product serial number",
            "convert": int,
        },
        "RESERVED": {
            "slice": (23, 20),
        },
        # "MDT": {  # combined layout for reference
        #    "slice": (19, 8),
        #    "name": "Manufacturing date",
        # },
        "MDT_Y": {
            "slice": (19, 12),
            "name": "Manufacturing date (year)",
            "convert": lambda v: v + 2000,
        },
        "MDT_M": {
            "slice": (11, 8),
            "name": "Manufacturing date (month)",
            "convert": lambda v: v + 1,
        },
        "CRC": {
            "slice": (7, 1),
            "name": "CRC7 checksum",
        },
        "NU1": {
            "slice": (0, 0),
            "name": "not used, always 1",
        },
    }


class SCR(RegisterDecoder):
    FIELDS = {
        "SCR_STRUCTURE": {
            "slice": (63, 60),
            "name": "SCR Structure",
            "enum": ["1.0"],
        },
        "SD_SPEC": {
            "slice": (59, 56),
            "name": "SD Memory Card - Spec. Version",
            "enum": ["1.0 or 1.01", "1.10", "2.00 or 3.0X"],
        },
        "DATA_STAT_AFTER_ERASE": {
            "slice": (55, 55),
            "name": "data status after erase",
            "convert": bool,
        },
        "SD_SECURITY": {
            "slice": (54, 52),
            "name": "CPRM Security Support",
            "enum": [
                "No Security",
                "Not Used",
                "SDSC Card (Security Version 1.01)",
                "SDHC Card (Security Version 2.00)",
                "SDXC Card (Security Version 3.xx)",
            ],
        },
        "SD_BUS_WIDTHS": {
            "slice": (51, 48),
            "name": "DAT Bus widths supported",
            "bits": ["1 bit", None, "4 bit", None],
        },
        "SD_SPEC3": {
            "slice": (47, 47),
            "name": "Spec. Version 3.00 or higher",
        },
        "EX_SECURITY": {
            "slice": (46, 43),
            "name": "Extended Security Support",
        },
        "RESERVED": {
            "slice": (42, 34),
        },
        "CMD_SUPPORT": {
            "slice": (33, 32),
            "name": "Command Support bits",
            "bits": ["Speed Class Control (CMD20)", "Set Block Count (CMD23)"],
        },
        "RESERVED_MFG": {
            "slice": (31, 0),
        },
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("input", help="input in JSON format", type=str)

    args = parser.parse_args()

    with open(args.input) as fd:
        data = json.loads(fd.read())

    if args.json:
        res = {}
        res["scr"] = SCR(data["scr"]["raw"]).decode()
        res["cid"] = CID(data["cid"]["raw"]).decode()
        res["csd"] = decode_csd(data["csd"]["raw"]).decode()
        print(json.dumps(res, indent=2))
    else:
        res = []
        res += decode_csd(data["csd"]["raw"]).get_text_report()
        res += SCR(data["scr"]["raw"]).get_text_report()
        res += CID(data["cid"]["raw"]).get_text_report()
        print("\n".join(res))
