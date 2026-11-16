"""Tests for calibration.py. Owner: add tests for YOUR conversion.
Run all tests with run_tests.py (press F5 in Thonny)."""

import calibration
import kit


def test_known_point_converts_correctly():
    # Raw counts for exactly 1.0 V should give SLOPE * 1.0 + INTERCEPT.
    data = kit.Data(0)
    data.data2 = 1.0 / calibration.V_REF * calibration.ADC_FULL_SCALE
    calibration.calibrate(data)
    expected = calibration.SLOPE + calibration.INTERCEPT
    assert data.ok
    assert abs(data.data4 - expected) < 0.01


def test_failed_read_passes_through():
    data = kit.Data(0)
    data.ok = False                     # the sensor module could not read
    calibration.calibrate(data)
    assert data.ok is False
    assert data.data4 is None

# TODO: a test that a reading at each end of your expected range gives a
# sensible value, using a reference point you measured yourself.
