# SPDX-License-Identifier: LGPL-2.1-or-later
# SPDX-FileCopyrightText: 2023 Pengutronix, Jan Lübbe <entwicklung@pengutronix.de>

import json
import os.path

import pytest

from usbsdmux.sd_regs import CID, SCR, decode_csd

REFS = [
    "02544d53413034471027b7748500bc00",
    "1b534d474638533530d8466363a16700",
    "744a605553442020104182bbc7010600",
    "9f5449303030303000a1114bb5011400",
]


@pytest.mark.parametrize("cid", REFS)
def test_decode(cid):
    ref_name = os.path.join(os.path.dirname(__file__), "reference", f"{cid}.json")

    with open(ref_name) as ref_file:
        ref = json.load(ref_file)

    res = {}
    res["scr"] = SCR(ref["scr"]["raw"]).decode()
    res["cid"] = CID(ref["cid"]["raw"]).decode()
    res["csd"] = decode_csd(ref["csd"]["raw"]).decode()

    # get rid of json differences, like [] -> ()
    res = json.loads(json.dumps(res))

    assert res == ref


@pytest.mark.parametrize("cid", REFS)
def test_to_text(cid):
    ref_name_json = os.path.join(os.path.dirname(__file__), "reference", f"{cid}.json")
    ref_name_text = os.path.join(os.path.dirname(__file__), "reference", f"{cid}.text")

    with open(ref_name_json) as ref_file_json:
        ref_json = json.load(ref_file_json)

    with open(ref_name_text) as ref_file_text:
        ref_text = ref_file_text.read().split("\n")[:-1]

    res = []

    res += decode_csd(ref_json["csd"]["raw"]).get_text_report()
    res += SCR(ref_json["scr"]["raw"]).get_text_report()
    res += CID(ref_json["cid"]["raw"]).get_text_report()

    assert res == ref_text
