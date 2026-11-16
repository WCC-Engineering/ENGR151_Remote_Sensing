"""
sensor.py -- SENSOR DRIVER MODULE
OWNER: ______________________

YOUR CONTRIBUTION
    read(sensor_data)   [function]

      * Stores raw sensor values on sensor_data, exactly as the sensor reports
        them (ADC counts, echo time in microseconds, register values, etc.).
        Converting to real units is the calibration module's job.

        Example: sensor_data.data2 = 23110

      * If a read fails, sets sensor_data.ok = False and leaves the value unset.

      * Never lets an exception escape. The rest of the system copes with a
        failed read; it cannot cope with a crash. I2C or serial devices can
        raise errors if they become disconnected unexpectedly.

THE EXAMPLE
    _read_sensor1() reads an analog sensor on ADC0, powering it through a MOSFET
    only while reading, and stores the raw ADC counts as data2. The other four
    slots are empty, ready for teams with more than one sensor.

POWER MANAGEMENT
    Switching the sensor off between reads (see SENSOR_POWER_PIN in config.py)
    saves energy when your node runs on a battery: a sensor that stays powered
    can use more energy than the rest of the node combined. Some sensors (many
    gas sensors, for example) need warm-up time after power-on. If yours does,
    say so in your proposal.

YOUR JOB
    1. Replace _read_sensor1() (and the other slots, if you need them) with code
       for your team's sensor. If your sensor has a MicroPython library, you will
       create its object and call its methods, the same way you use machine.Pin
       and machine.ADC.
    2. Handle the ways your sensor can fail (no response, timeout, a reading
       outside what the sensor can physically report).
    3. Keep _read_fake() working and make it resemble YOUR sensor's raw output,
       because your teammates use it to test their modules without hardware.
       It runs while USE_FAKE_SENSOR is True in config.py.
    4. Once you know what each value is, rename data1 to data5 to meaningful
       names with units, together with your teammates (see telemetry.py).
"""

import math
import random

import config

SETTLE_MS = 50      # time for the sensor to stabilize after power-on
N_SAMPLES = 16      # readings averaged together to reduce noise

_fake_step = 0      # counts fake readings so the fake signal changes over time


def read(sensor_data):
    try:
        if config.USE_FAKE_SENSOR:
            _read_fake(sensor_data)
        else:
            _read_sensor1(sensor_data)
            _read_sensor2(sensor_data)
            _read_sensor3(sensor_data)
            _read_sensor4(sensor_data)
            _read_sensor5(sensor_data)
    except Exception as err:        # Ctrl+C still stops the program
        print("sensor read failed:", err)
        sensor_data.ok = False


def _read_sensor1(sensor_data):
    """EXAMPLE: an analog sensor on ADC0, powered only while reading."""
    import machine
    import time
    power = machine.Pin(config.SENSOR_POWER_PIN, machine.Pin.OUT)
    adc = machine.ADC(config.SENSOR_ADC0_PIN)
    power.value(1)
    try:
        time.sleep_ms(SETTLE_MS)
        total = 0
        for _ in range(N_SAMPLES):
            total += adc.read_u16()
            time.sleep_ms(2)
    finally:
        power.value(0)      # always switch the sensor off, even if something failed
    sensor_data.data2 = total // N_SAMPLES


def _read_sensor2(sensor_data):
    pass


def _read_sensor3(sensor_data):
    pass


def _read_sensor4(sensor_data):
    pass


def _read_sensor5(sensor_data):
    pass


def _read_fake(sensor_data):
    """Made-up raw ADC counts that look like a real signal: a steady baseline,
    one event that rises over two hours and fades over several more, sensor
    noise, and an occasional failed read. Event timing follows the simulated
    clock, so it looks the same whatever SAMPLE_SECONDS is."""
    global _fake_step
    step = _fake_step
    _fake_step += 1

    if step % 53 == 17:                     # now and then the sensor just fails
        sensor_data.ok = False
        return

    hours = step * config.SAMPLE_SECONDS / 3600
    baseline = 12000
    start, rise_hours, peak = 15.0, 2.0, 20000
    k = hours - start
    if k < 0:
        event = 0
    elif k < rise_hours:
        event = peak * k / rise_hours                       # steady rise
    else:
        event = peak * math.exp(-(k - rise_hours) / 5)      # slow fade

    noise = random.getrandbits(7) - 64                      # about +/- 64 counts
    sensor_data.data2 = int(baseline + event + noise)
