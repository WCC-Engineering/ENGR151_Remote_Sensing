"""Tests for telemetry.py. Owner: add tests for YOUR check() rules."""

import kit          # the simulator's fake kit (see run_tests.py)
import telemetry


def good_sample():
    data = kit.Data(1_000_000)
    data.data1 = 12
    data.data2 = 23110
    data.data3 = 123.4
    data.data4 = 123.45
    data.data5 = False
    return data


def test_payload_matches_template_types():
    payload = kit.pack(good_sample(), telemetry.DATA_FIELDS)
    assert set(payload) == set(telemetry.DATA_FIELDS)
    for name, hint in telemetry.DATA_FIELDS.items():
        if hint is True:
            assert isinstance(payload[name], bool), name
        elif isinstance(hint, float):
            assert isinstance(payload[name], float), name
        else:
            assert isinstance(payload[name], int), name


def test_bad_sample_sends_missing_numbers():
    data = good_sample()
    data.ok = False
    payload = kit.pack(data, telemetry.DATA_FIELDS)
    for name, hint in telemetry.DATA_FIELDS.items():
        if hint is not True:
            assert payload[name] == kit.MISSING, name


def test_every_field_is_set_by_the_modules():
    # Run one fake sample through all the modules. Catches a name in
    # DATA_FIELDS that no module sets (usually a spelling mismatch).
    import config, sensor, calibration, processing
    config.USE_FAKE_SENSOR = True
    kit.reset_memory()
    for i in range(2):                  # the rate needs two samples
        data = kit.Data(1_000_000 + i * 900)
        sensor.read(data)
        calibration.calibrate(data)
        processing.process(data)
    if data.ok:
        assert kit.unset_fields(data, telemetry.DATA_FIELDS) == []


def test_check_marks_unbelievable_values_bad():
    data = good_sample()
    data.data1 = telemetry.MAX_RATE * 10
    telemetry.check(data)
    assert data.ok is False
    data = good_sample()
    telemetry.check(data)
    assert data.ok is True


def test_notecard_accepts_sample():
    node = kit.Node()
    node.setup(telemetry.DATA_FIELDS)
    assert "err" not in node.add_data(good_sample())
