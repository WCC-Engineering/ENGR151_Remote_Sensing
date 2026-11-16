"""
processing.py -- SIGNAL PROCESSING MODULE
OWNER: ______________________

YOUR CONTRIBUTION
    process(sensor_data)    [function]

      * Starts from the calibrated values stored on sensor_data and adds the
        values your team reports: cleaned-up values, derived metrics, and
        event flags.

      * Every value your team sends must also appear in telemetry.DATA_FIELDS,
        with exactly the same name.

REMEMBERING EARLIER SAMPLES
    Smoothing, rates, and events all depend on earlier samples. The objects
    created below the settings remember what they need from one cycle to the
    next (and through a reboot), so your function never has to. Create them
    once, at the top of the file, the same way you would create a machine.Pin,
    then call their methods inside process(). See kit_data.py for what each offers.

THE EXAMPLE
    1. Range check: discard physically impossible values of data4.
    2. Smoothing: data3 is a moving average of the last WINDOW good values.
    3. Rate of change: data1 is how fast data3 is changing, in units per hour.
    4. Event detection with hysteresis: data5 turns on when the value climbs
       faster than RISE_ON and turns off only when the rate drops below
       RISE_OFF. Two thresholds keep noise near one threshold from making the
       flag flicker on and off.

YOUR JOB
    Adapt this to your team's question. What does a meaningful event look like
    in your data? What number would help someone make a decision? Tune the
    settings against real or simulated data, and be ready to justify them.
"""

import kit

# Settings: tune these, and be ready to explain your choices.
WINDOW = 10                     # samples in the moving average
LOW = 0.0                       # anything outside LOW to HIGH is a bad read
HIGH = 2000.0
RISE_ON = 40.0                  # event starts above this rate (units per hour)
RISE_OFF = 10.0                 # event ends below this rate

# Objects that remember earlier samples.
smoother = kit.RollingAverage(WINDOW)
rate = kit.RateOfChange()
rising = kit.Trigger(on=RISE_ON, off=RISE_OFF)


def process(sensor_data):
    value = sensor_data.data4

    if not sensor_data.ok or value is None or value < LOW or value > HIGH:
        sensor_data.ok = False                  # its numbers are sent as "missing"
        sensor_data.data5 = rising.active       # an event in progress stays on
        return

    sensor_data.data3 = smoother.add(value)
    per_hour = rate.update(sensor_data.data3, sensor_data.time)
    sensor_data.data1 = None if per_hour is None else round(per_hour)
    sensor_data.data5 = rising.update(per_hour)
