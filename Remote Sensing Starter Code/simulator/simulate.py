"""
simulate.py -- run your team's Pico modules on your laptop.

Uses the fake sensor, a fake Notecard, and a simulated clock, so two days of
samples take a few seconds. Every sample lands in
simulator/output/sim_events.jsonl, which laptop/analyze.py and
laptop/send_to_datacake.py can use exactly like exported real data.

Your modules say "import kit", but the Pico's kit.py needs the Pico's hardware.
So this file loads fake_kit.py and registers it under the name "kit" before
loading your modules. They get the fake one without knowing the difference.

In Thonny: open this file and press F5, with the interpreter set to Local Python 3.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PICO = os.path.normpath(os.path.join(HERE, "..", "pico"))
if PICO not in sys.path:
    sys.path.insert(1, PICO)

import fake_kit                 # noqa: E402
sys.modules["kit"] = fake_kit   # from here on, "import kit" means the fake kit

import config                   # noqa: E402
import kit                      # noqa: E402  (the fake kit, registered above)
import main                     # noqa: E402  (pico/main.py)
import sensor                   # noqa: E402
import telemetry                # noqa: E402

HOURS = 48
OUT = os.path.join(HERE, "output", "sim_events.jsonl")


def simulate(hours=HOURS, out_path=OUT):
    """Run the team's modules for the given number of simulated hours.
    Returns the number of samples taken."""
    config.USE_FAKE_SENSOR = True
    sensor._fake_step = 0
    kit.reset_memory()
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    if os.path.exists(out_path):
        os.remove(out_path)

    node = kit.Node(out_path)
    node.connect(verbose=False)
    node.setup(telemetry.DATA_FIELDS)
    n = int(hours * 3600 / config.SAMPLE_SECONDS)
    for _ in range(n):
        try:
            main.run(node)
        except Exception as err:
            node.error(err)
        node.sleep()
    return n


if __name__ == "__main__":
    n = simulate()
    print(f"Simulated {n} samples ({HOURS} h). Data written to {OUT}")
    print("Next: open laptop/analyze.py and press F5.")
