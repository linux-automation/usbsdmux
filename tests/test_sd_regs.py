import os.path
import json

import pytest

from usbsdmux.sd_regs import SCR, CID, decode_csd

REFS = [
    "02544d53413034471027b7748500bc00",
    "1b534d474638533530d8466363a16700",
    "744a605553442020104182bbc7010600",
    "9f5449303030303000a1114bb5011400",
]


@pytest.mark.parametrize("cid", REFS)
def test_decode(cid):
    ref_name = os.path.join(os.path.dirname(__file__), "reference", f"{cid}.json")
    ref = json.load(open(ref_name))

    res = {}
    res["scr"] = SCR(ref["scr"]["raw"]).decode()
    res["cid"] = CID(ref["cid"]["raw"]).decode()
    res["csd"] = decode_csd(ref["csd"]["raw"]).decode()

    # get rid of json differences, like [] -> ()
    res = json.loads(json.dumps(res))

    assert res == ref
