"""
telemetry.py -- TELEMETRY MODULE
OWNER: ______________________

YOUR CONTRIBUTION
    DATA_FIELDS             [variable]

      * Defines the data your node sends: the names and types shared by the
        Notecard and your Datacake dashboard.

    check(sensor_data)      [function]

      * Marks the sample bad (sensor_data.ok = False) if anything about it is
        not believable at your site.

WHY DATA_FIELDS
    The Notecard LoRa sends data using a template: every field has a fixed name
    and type, packed into a very small radio message.

    node.add_data(sensor_data) takes the values in sensor_data, converts them to
    the types listed in DATA_FIELDS, and passes them to the Notecard to send.

      * Every value your team sends must appear in DATA_FIELDS with exactly the
        same name.
      * Values in sensor_data that are not in DATA_FIELDS are not sent.
      * A name in DATA_FIELDS that no module sets is sent as kit.MISSING (-9999),
        and the node prints a warning so you can fix the spelling.
      * On a sample marked bad (ok is False), every number is sent as kit.MISSING.
      * Templated notes drop fields whose value is 0 or false. The decoder and
        laptop/load_events.py put them back.

TEMPLATE TYPE HINTS (from the Blues documentation)
    12    2-byte signed integer (-32768 to 32767)
    14    4-byte signed integer (about +/- 2 billion)
    12.1  2-byte float (about 3 significant digits)
    14.1  4-byte float (about 7 significant digits)
    True  boolean

THE EXAMPLE
    The five fields show each type, filled in by the example modules:
        data1  rate of change, units per hour     (processing.py)
        data2  raw ADC counts                     (sensor.py)
        data3  smoothed value                     (processing.py)
        data4  calibrated value                   (calibration.py)
        data5  event flag                         (processing.py)

YOUR JOB
    * Rename and retype the fields for your project, with names that include
      units (level_mm, temp_c). Keep DATA_FIELDS in agreement with the other
      modules and with your dashboard's decoder (datacake/decoder.js). You own
      that agreement: if a name changes here, it changes there.
    * Write check() rules for your data: values that are physically possible but
      not believable at your site, or combinations that should never happen.
    * Keep the payload small. A few numbers per sample is the right size.
"""

DATA_FIELDS = {
    "data1": 12,
    "data2": 14,
    "data3": 12.1,
    "data4": 14.1,
    "data5": True,
}

# Limits for check(). Set these from what is believable at your site.
MAX_RATE = 5000         # data1: a faster change than this is a sensor glitch


def check(sensor_data):
    if not sensor_data.ok:
        return                              # already marked bad upstream
    if sensor_data.data1 is not None and abs(sensor_data.data1) > MAX_RATE:
        print("data1 is not believable:", sensor_data.data1)
        sensor_data.ok = False
