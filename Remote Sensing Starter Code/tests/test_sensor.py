"""Tests for sensor.py. Owner: add tests for YOUR sensor's raw values."""

import config
import kit
import sensor


def fake_samples(n):
    config.USE_FAKE_SENSOR = True
    sensor._fake_step = 0
    samples = []
    for i in range(n):
        data = kit.Data(i)
        sensor.read(data)
        samples.append(data)
    return samples


def test_fake_read_gives_raw_counts():
    # Good fake reads store raw ADC counts: a whole number from 0 to 65535.
    for data in fake_samples(100):
        if data.ok:
            assert isinstance(data.data2, int)
            assert 0 <= data.data2 <= 65535


def test_fake_reader_sometimes_fails():
    # The fake reader fails now and then, so teammates' code gets practice
    # handling a bad sample. Keep this true when you rewrite _read_fake().
    samples = fake_samples(100)
    assert any(not d.ok for d in samples)
    assert sum(d.ok for d in samples) > 90


def test_hardware_error_marks_sample_bad_instead_of_crashing():
    # Pretend the real sensor is unplugged: its read raises an error.
    def broken(sensor_data):
        raise OSError("sensor not responding")
    real = sensor._read_sensor1
    config.USE_FAKE_SENSOR = False
    sensor._read_sensor1 = broken
    try:
        data = kit.Data(0)
        sensor.read(data)               # must not raise
        assert data.ok is False
    finally:
        sensor._read_sensor1 = real
        config.USE_FAKE_SENSOR = True
