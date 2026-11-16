# ENGR 151 Connected Sensor: Team Starter Files

Start here. These files hold everything your team needs to build, test, and analyze your connected sensor. Unzip them into the `code` folder of your team's shared Google Drive or OneDrive folder, and see *Team Roles and Code Ownership* on Canvas for how to share and track changes.

## What's inside

```
pico/                          everything that goes on the Pico, and nothing else
  main.py                      runs each sample through the four modules below
  config.py                    team settings: ProductUID, timing, sleep, pins
  kit.py                       supplied: the node (Notecard, time, sending, sleep)
  kit_data.py                  supplied: the Data object and the memory objects
  sensor.py                    owner: sensor driver
  calibration.py               owner: calibration
  processing.py                owner: signal processing
  telemetry.py                 owner: telemetry (DATA_FIELDS)
  lib/notecard/                the Blues note-python library
simulator/                     laptop only: runs your pico/ modules with fake data
  simulate.py                  two days of fake samples in a few seconds
  fake_kit.py                  stand-in for pico/kit.py with a fake Notecard and clock
laptop/                        analysis tools that run on your computer
  fit_calibration.py           owner: calibration
  analyze.py                   owner: analysis and display
  load_events.py               loads simulator output, Notehub exports, or Datacake CSVs
  send_to_datacake.py          sends simulated samples to your Datacake dashboard
  sample_data/                 example calibration points and example data
datacake/
  decoder.js                   paste into Datacake's HTTP Payload Decoder (owner: telemetry)
  sample_webhook.json          an example Notehub message for Datacake's "Try Decoder"
tests/                         one test file per module, plus a whole-system test
run_tests.py                   runs every test with the simulator: open it in Thonny, press F5
```

The project brief, the data path guide, the dashboard guide, and the team roles page are on Canvas, along with the Word templates for your team agreement and purchase proposal.

## How the modules connect

`main.py` creates one `Node`, your sensor node, and gets a new `Data` object from it for each sample. Each module fills in its part:

```
node = kit.Node()
node.connect()                       finds the Notecard
node.setup(telemetry.DATA_FIELDS)    tells Notehub and the Notecard what you send

sensor_data = node.new_data()        each sample, stamped with the time
sensor.read(sensor_data)             raw values          (example: data2)
calibration.calibrate(sensor_data)   real units          (example: data4)
processing.process(sensor_data)      smoothed values, rates, event flags (data3, data1, data5)
telemetry.check(sensor_data)         marks it bad if it is not believable
node.add_data(sensor_data)           queues the values named in DATA_FIELDS
node.sleep()                         waits until the next sample
```

You never write a class. You use the supplied ones the way you use `machine.Pin`: create an object, then call its methods. The processing module also uses three supplied objects that remember earlier samples: `RollingAverage`, `RateOfChange`, and `Trigger`.

## The five data fields

The starter files send five placeholder fields, one of each template type, so you can see how each works:

| Field | Type | Example meaning | Set by |
|---|---|---|---|
| `data1` | 2-byte integer (`12`) | rate of change per hour | processing.py |
| `data2` | 4-byte integer (`14`) | raw ADC counts | sensor.py |
| `data3` | 2-byte float (`12.1`) | smoothed value | processing.py |
| `data4` | 4-byte float (`14.1`) | calibrated value | calibration.py |
| `data5` | boolean (`True`) | event flag | processing.py |

When your team knows what it is measuring, rename the fields together, with units in the names (`level_mm`, `temp_c`). A name has to change in four places at once: `telemetry.DATA_FIELDS`, the module that sets it, `datacake/decoder.js`, and your Datacake fields. `run_tests.py` catches most mismatches.

## Two ways to run the same modules

Your four modules live in `pico/`, and only there. Two programs run them:

* **On the Pico**, `pico/main.py` runs them with the real Notecard.
* **On your laptop**, `simulator/simulate.py` and `run_tests.py` run the same files with a fake sensor and a fake Notecard, so you can test before your parts arrive. Your modules say `import kit`; on the laptop, these programs hand them `simulator/fake_kit.py` instead of the Pico's `kit.py`.

Nothing in `simulator/` or `laptop/` is copied onto the Pico.

## First day: run everything on your laptop

Everything below runs in Thonny on your laptop, not on the Pico.

1. In the bottom-right corner of Thonny, switch the interpreter to **Local Python 3**.
2. Install pandas and matplotlib once: Tools > Manage packages.
3. Open `run_tests.py` and press F5. Expect "All 18 tests passed".
4. Open `simulator/simulate.py` and press F5. It writes two days of simulated samples.
5. Open `laptop/analyze.py` and press F5. It analyzes the simulated samples and saves a figure in `laptop/output/`.

To test only your own module while you work, set `ONLY` near the top of `run_tests.py`, for example `ONLY = "test_processing"`.

If all the tests pass and `analyze.py` saves a figure, the whole system works with a fake sensor, and each owner can start adapting their module. Next, follow *Building Your Datacake Dashboard* on Canvas to send the same simulated data to a live dashboard.

## Putting it on the Pico

1. In `config.py`, set `PRODUCT_UID` to your Notehub project's ProductUID.
2. Copy everything in `pico/` onto the Pico, including the `lib` folder.
3. In the Pico's REPL, run `import kit; kit.Node().connect(verbose=True)`. It lists what is on the I²C bus and confirms the Notecard answers.
4. Leave `USE_FAKE_SENSOR = True` until your real sensor is wired and `sensor.py` works.
5. Reset the Pico. `main.py` starts automatically. The first time it runs, it clears old settings off the Notecard and checks the LoRa connection, which can take a minute or two.

The first-run clearing happens only when there is no `state.json` on the Pico. Do not copy a `state.json` from another Pico.

### Before you deploy

The defaults in `config.py` are for testing: a sample every 30 seconds, uploads every minute, and no sleep. Before the node goes into the field, set `SAMPLE_SECONDS` to 300 or more, choose `OUTBOUND_MINUTES`, and on battery or solar power set `SLEEP_BETWEEN_SAMPLES = True`. Read the comments in `config.py` first: with sleep on, Thonny can no longer connect to the Pico while it runs.

Then follow *From Sensor to Dashboard* on Canvas to confirm each hop from the Pico to your dashboard.
