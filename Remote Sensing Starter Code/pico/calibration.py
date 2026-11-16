"""
calibration.py -- CALIBRATION MODULE
OWNER: ______________________

YOUR CONTRIBUTION
    calibrate(sensor_data)  [function]

      * Converts the raw values the sensor module stored into engineering
        units, stored on the same sensor_data. In the example, raw ADC counts
        (data2) become a calibrated value (data4).

      * If the reading already failed (sensor_data.ok is False), leaves it alone.

WHERE THE NUMBERS COME FROM
    1. Take reference measurements: set up known conditions (a ruler in a bucket,
       a trusted thermometer) and record the raw reading at each one. Aim for at
       least five points spread across the range you expect in the field.
    2. Save them as a CSV like laptop/sample_data/calibration_points.csv.
    3. Run laptop/fit_calibration.py on your points and paste the coefficients
       it prints into SLOPE and INTERCEPT below.

YOUR JOB
    Replace the example with the conversion your sensor needs. A straight line is
    a starting point, not a requirement: if your residuals show a curve, fit one.
    Be ready to explain how you know your calibration is good. When you rename
    data1 to data5, put the units in the names (level_mm, temp_c, co2_ppm) so
    nobody has to guess.
"""

# Pico ADC values. Replace or add values as your sensor needs.
ADC_FULL_SCALE = 65535
V_REF = 3.3

# EXAMPLE VALUES. Replace with the output of laptop/fit_calibration.py.
SLOPE = 250.0          # units per volt
INTERCEPT = -50.0      # units


def counts_to_volts(counts):
    return counts * V_REF / ADC_FULL_SCALE


def calibrate(sensor_data):
    if not sensor_data.ok:
        return
    volts = counts_to_volts(sensor_data.data2)
    sensor_data.data4 = SLOPE * volts + INTERCEPT
