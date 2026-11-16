"""Whole-system test: every module working together through the simulator.
If your module passes its own tests but this fails, the problem is usually
an interface: a field name, a type, or a missing value."""

import os
import tempfile

from load_events import load_events
from simulate import simulate
from telemetry import DATA_FIELDS


def test_full_pipeline():
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "events.jsonl")
        n = simulate(hours=48, out_path=out)
        df = load_events(out, DATA_FIELDS)
    assert len(df) == n
    assert set(DATA_FIELDS) <= set(df.columns)
    assert df["data5"].any(), "the simulated event should be detected"
    assert not df["data5"].iloc[-1], "and should have ended by the end"
    # Failed reads must come back as NaN, not 0, even though LoRa drops zeros.
    assert df["data4"].isna().mean() > 0
    assert df["data4"].notna().mean() > 0.9


def test_field_that_is_always_false_still_loads():
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "events.jsonl")
        with open(out, "w") as f:
            f.write('{"when": 1790000000, "body": {"data4": 100.0}}\n')
        df = load_events(out, DATA_FIELDS)
    assert "data5" in df.columns and not df["data5"].any()
