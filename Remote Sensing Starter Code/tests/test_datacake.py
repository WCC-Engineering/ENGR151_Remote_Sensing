"""Checks that the replay tool builds the same envelope Notehub sends, and that
the Datacake decoder's field list matches telemetry.DATA_FIELDS."""

import os
import re

from send_to_datacake import notehub_envelope
from telemetry import DATA_FIELDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_envelope_matches_notehub_shape():
    ev = {"file": "data.qo", "when": 1000, "body": {"data4": 5.0}}
    env = notehub_envelope(ev, "dev:123", shift=60)
    assert env["device"] == "dev:123"
    assert env["file"] == "data.qo"
    assert env["when"] == 1060
    assert env["body"] == {"data4": 5.0}


def test_decoder_fields_match_telemetry():
    js = open(os.path.join(ROOT, "datacake", "decoder.js")).read()
    block = re.search(r"var DATA_FIELDS = \{(.*?)\};", js, re.S).group(1)
    js_fields = dict(re.findall(r"[\"']?(\w+)[\"']?\s*:\s*[\"'](\w+)[\"']", block))
    assert set(js_fields) == set(DATA_FIELDS), \
        "decoder.js DATA_FIELDS must have the same names as telemetry.DATA_FIELDS"
    for name, hint in DATA_FIELDS.items():
        expected = "boolean" if hint is True else "number"
        assert js_fields[name] == expected, \
            "decoder.js says " + name + " is " + repr(js_fields[name]) + "; it should be " + repr(expected)
