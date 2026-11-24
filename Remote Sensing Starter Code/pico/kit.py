"""
kit.py -- SUPPLIED PLATFORM CODE FOR THE PICO. PLEASE DO NOT EDIT.

This file gives you one object, the node, that handles everything your
instructor has already worked out: talking to the Notecard LoRa, setting up
Notehub, timestamps, sending readings, sleeping between samples, and saving what
must survive a reboot.
main.py uses it like this:

    node = kit.Node()
    node.connect()                      find the Notecard and say hello
    node.setup(telemetry.DATA_FIELDS)   tell Notehub and the Notecard what you send
    data = node.new_data()              a fresh Data object, stamped with the time
    node.add_data(data)                 queue the data for upload
    node.sleep()                        wait until the next sample
    node.check_connection()             sync now and check the LoRa link works

How often the node samples and uploads, and whether it sleeps in between, is set
in config.py (SAMPLE_SECONDS, OUTBOUND_MINUTES, SLEEP_BETWEEN_SAMPLES).

It also passes along the objects your modules use (kit.Data, kit.RollingAverage,
kit.RateOfChange, kit.Trigger), which live in kit_data.py.

This file runs only on the Pico. On a laptop, the simulator folder has a
stand-in kit.py with the same methods and a fake Notecard.

If something in here looks wrong, talk to your instructor instead of changing it.
"""

import json
import sys
import time

import machine
import notecard     # note-python library, copied onto the Pico

import config
# Imported here so modules can write kit.RollingAverage, kit.Data, and so on.
from kit_data import (MISSING, Data, RollingAverage, RateOfChange, Trigger,
                      reset_memory, save_memory, restore_memory,
                      pack, unset_fields)

# ---------------------------------------------------------------------------
# Platform settings (instructor-owned).
# ---------------------------------------------------------------------------
NOTECARD_ADDRESS = 0x17         # the Notecard's I2C address

MIN_DEPLOYED_SAMPLE_SECONDS = 300   # sampling faster than this only prints a warning (LoRa airtime limits)

DATA_NOTEFILE = "data.qo"       # .qo = queue, outbound (device to cloud)

CONNECT_CHECK_SECONDS = 300     # how long the connection check waits. Far from the gateway, joining the
                                # LoRaWAN network can take several tries, a few minutes apart.

LORA_PORT = 50                  # each LoRa template needs its own port number, 1 to 100

STATE_FILE = "state.json"


class Node:
    """Your sensor node: the Pico plus its Notecard."""

    def __init__(self):
        self.card = None
        self.data_fields = {}

        self.state = self._load_state()
        restore_memory(self.state)

        # 100 kHz, not MicroPython's default 400 kHz: the Notecard's 10K pull-up
        # resistors and jumper-wire connections are too slow for 400 kHz to be reliable.
        self.i2c = machine.I2C(config.I2C_ID,
                               sda=machine.Pin(config.I2C_SDA),
                               scl=machine.Pin(config.I2C_SCL),
                               freq=100000)

    # -- connecting -------------------------------------------------------------
    def connect(self, verbose=False):
        """Look for the Notecard on the I2C bus and open a connection.
        Returns True if it is there. With verbose=True, prints what it finds,
        which makes this the first thing to run when the Notecard is not responding."""
        found = self.i2c.scan()
        if verbose:
            print("I2C devices found:", [hex(a) for a in found])
        if NOTECARD_ADDRESS not in found:
            print("Notecard (0x17) NOT found. Check wiring, power, and the I2C pins in config.py.")
            return False
        try:
            self.card = notecard.OpenI2C(self.i2c, 0, 0)
        except Exception as err:
            self.card = None
            print("Notecard answered at 0x17 but did not respond to requests:", err)
            print("  1. Unplug the USB cable for 10 seconds, plug it back in, and try once more.")
            print("  2. Check the power wire: Pico VBUS (pin 40) to the Notecarrier's VUSB.")
            print("  3. Press each of the four wires firmly onto its pin, or swap in new wires.")
            return False
        if verbose:
            version = self.request({"req": "card.version"})
            print("Notecard found at 0x17:", version.get("device"))
        return True

    def request(self, req, quiet=False):
        """Send one JSON request to the Notecard and return its response dictionary.
        Any error comes back as {"err": "..."} and is printed so you can see it
        (unless quiet=True)."""
        if self.card is None:
            return {"err": "not connected; run node.connect() first"}
        try:
            rsp = self.card.Transaction(req)
        except Exception as err:
            rsp = {"err": "transaction failed: " + str(err)}
        if "err" in rsp and not quiet:
            print("Notecard error on", req.get("req"), "->", rsp["err"])
        return rsp

    # -- setting up ---------------------------------------------------------------
    def setup(self, data_fields):
        """Tell Notehub where to send data and how often to upload, and tell the
        Notecard the shape of each reading (the template). Only sends requests
        when something has changed, because each different template is stored on
        the Notecard as a new one."""

        self.data_fields = data_fields

        # First run of this code on this Pico: the Notecard may still hold templates
        # and settings from an earlier project, so wipe it before configuring it.
        first_run = False
        if not self.state.get("notecard_cleared"):
            if self._clear_notecard():
                first_run = True
                self.state.pop("hub_setup", None)       # everything must be sent again
                self.state.pop("templates", None)
                self.state["notecard_cleared"] = True
                self._save_state()

        outbound = self.outbound_minutes()

        # Remember what was last sent, so a changed setting is noticed on the next
        # start-up. Upload settings and templates are tracked separately: changing
        # OUTBOUND_MINUTES does not send new templates.
        hub_sig = json.dumps([config.PRODUCT_UID, outbound])
        template_sig = json.dumps([[k, v] for k, v in sorted(data_fields.items())])
        self.state.pop("kit_setup", None)       # old format, no longer used

        if self.state.get("hub_setup") != hub_sig:
            rsp = self.request({"req": "hub.set",
                                "product": config.PRODUCT_UID,
                                "mode": "periodic",
                                "outbound": outbound})
            if "err" not in rsp:
                self.state["hub_setup"] = hub_sig

        if self.state.get("templates") != template_sig:
            # LoRa requires a compact template with a port number. Compact format
            # drops the timestamp unless we ask for it back with the special _time field.
            body = dict(data_fields)
            body["_time"] = 14
            rsp = self.request({"req": "note.template", "file": DATA_NOTEFILE,
                                "format": "compact", "port": LORA_PORT, "body": body})
            if "err" not in rsp:
                self.state["templates"] = template_sig

        self._save_state()

        if config.SAMPLE_SECONDS < MIN_DEPLOYED_SAMPLE_SECONDS:
            print("note: SAMPLE_SECONDS is under", MIN_DEPLOYED_SAMPLE_SECONDS,
                  "seconds. Fine for testing, but set it back before you deploy.")
        print("Sampling every", self.sample_seconds(), "seconds, uploading every",
              outbound, "minutes, low-power sleep",
              "ON" if config.SLEEP_BETWEEN_SAMPLES else "OFF")

        # First run only: sync with Notehub right away and check that the LoRa link
        # works, so problems show up now instead of after the first upload interval.
        if first_run:
            self.check_connection()

    def _clear_notecard(self):
        """Wipe old templates, queued notes, and settings off the Notecard. Runs
        once, the first time this code runs on this Pico, i.e. when state.json has
        no "notecard_cleared" entry. Deleting state.json makes it run again.

        Uses card.restore with delete=True, which also erases the Notecard's
        settings (setup() sends them again right afterwards).
        Returns True if the Notecard accepted the reset. It returns True even if
        the Notecard is slow to answer afterwards, so the reset is never repeated
        on the next power-up: each reset erases queued data and makes the Notecard
        join the LoRaWAN network again, which may not work far from the gateway."""
        print("First run: clearing old templates from the Notecard...")
        rsp = self.request({"req": "card.restore", "delete": True})   # replies {}, then restarts
        if "err" in rsp:
            return False
        if not self._wait_for_notecard():
            return True
        if self._old_templates():
            print("warning: an old template may still be on the Notecard; ask your instructor")
        else:
            print("Notecard cleared.")
        return True

    def _wait_for_notecard(self):
        """After a restart, wait until the Notecard answers again."""
        time.sleep(3)
        for _ in range(15):
            if "err" not in self.request({"req": "card.version"}, quiet=True):
                return True
            time.sleep(2)
        print("warning: the Notecard did not answer after restarting")
        return False

    def _old_templates(self):
        """True if the Notecard still has a template on our notefile."""
        rsp = self.request({"req": "note.template", "file": DATA_NOTEFILE, "verify": True},
                           quiet=True)
        return bool(rsp.get("template"))

    # -- each sample ----------------------------------------------------------------
    def time(self):
        """Current time in UNIX seconds, from the Notecard's network clock."""
        rsp = self.request({"req": "card.time"}, quiet=True)
        t = rsp.get("time")
        if not t:
            # The Notecard has not synced its clock yet; estimate from the last known time.
            t = self.state.get("last_time", 0) + self.sample_seconds()
        self.state["last_time"] = t
        return t

    def new_data(self):
        """A fresh Data object, stamped with the current time."""
        return Data(self.time())

    def add_data(self, data):
        """Print the data, pack the values named in DATA_FIELDS, and queue them
        on the Notecard. The Notecard uploads them at the OUTBOUND_MINUTES interval."""
        if data.ok:
            for name in unset_fields(data, self.data_fields):
                print("warning: no module set data." + name + "; check the spelling")

        req = {"req": "note.add", "file": DATA_NOTEFILE,
               "body": pack(data, self.data_fields)}
        return self.request(req)

    def sync(self):
        """Ask the Notecard to connect to Notehub and upload right now.
        "allow": True also lifts the Notecard's retry back-off (its "penalty box").
        After several failed tries, for example far from the gateway, the Notecard
        waits longer and longer between attempts, even after it is moved closer.
        If the Notecard rejects "allow", the plain request is sent instead."""
        rsp = self.request({"req": "hub.sync", "allow": True}, quiet=True)
        if "err" in rsp:
            rsp = self.request({"req": "hub.sync"})
        return rsp

    def check_connection(self, wait_seconds=CONNECT_CHECK_SECONDS):
        """Sync with Notehub now and wait to see whether the LoRa link works.
        Prints the Notecard's status as it changes. Returns True if a sync
        completed (the Notecard joined the LoRaWAN network through a gateway
        and reached Notehub), False if it had not within wait_seconds.
        Students can also call this any time: node.check_connection()"""
        if self.card is None and not self.connect():
            return False
        print("Syncing with Notehub over LoRa. This can take a few minutes,")
        print("longer far from the gateway. Waiting up to", wait_seconds, "seconds...")
        rsp = self.sync()
        if "err" in rsp:
            print("Could not start a sync:", rsp["err"])
            return False
        last = None
        waited = 0
        while waited < wait_seconds:
            time.sleep(5)
            waited += 5
            rsp = self.request({"req": "hub.sync.status"}, quiet=True)
            status = rsp.get("status") or rsp.get("err")
            if status != last:
                print("  Notecard:", status)
                last = status
            elif waited % 30 == 0:
                print("  still waiting,", waited, "seconds so far")
            # A finished sync reports "completed" (seconds since it finished) and no
            # longer reports "requested". Either sign that a sync finished after we
            # asked for one counts as success.
            completed = rsp.get("completed")
            if completed is not None and (not rsp.get("requested") or completed <= waited + 5):
                print("LoRa connection OK: the Notecard reached Notehub.")
                return True
        hub = self.request({"req": "hub.status"}, quiet=True)
        print("No sync yet after", wait_seconds, "seconds. hub.status:",
              hub.get("status") or hub.get("err"))
        print("  This is not necessarily a failure: the Notecard keeps trying on its own.")
        print("  Leave the program running and watch Events in Notehub for 10 minutes.")
        print("  If nothing arrives, check that the antenna is attached and pointing up,")
        print("  move closer to the gateway, or wait longer: node.check_connection(600)")
        return False

    # -- between samples ------------------------------------------------------------
    def sample_seconds(self):
        """Seconds between samples, from config.py (at least 1)."""
        return max(1, config.SAMPLE_SECONDS)

    def outbound_minutes(self):
        """Minutes between uploads, from config.py (a whole number, 1 or more)."""
        return max(1, int(config.OUTBOUND_MINUTES))

    def sleep(self, seconds=None):
        """Save what must survive a reboot, then wait until the next sample.
        With SLEEP_BETWEEN_SAMPLES = False in config.py the Pico stays awake, so
        USB and the REPL keep working. With True it uses the Pico's low-power
        sleep, which saves energy but switches USB off while it sleeps."""
        self._save_state()
        if seconds is None:
            seconds = self.sample_seconds()
        if config.SLEEP_BETWEEN_SAMPLES:
            machine.lightsleep(int(seconds * 1000))
        else:
            time.sleep(seconds)

    def error(self, err):
        """Count the error, print it so you can see what went wrong, and keep
        going: a node in the field should never die from one bad sample."""
        self.state["errors"] = self.state.get("errors", 0) + 1
        print("cycle failed, continuing:")
        sys.print_exception(err)

    # -- saved state ------------------------------------------------------------------
    def _load_state(self):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _save_state(self):
        save_memory(self.state)
        try:
            with open(STATE_FILE, "w") as f:
                f.write(json.dumps(self.state))
        except (OSError, TypeError, ValueError) as err:
            print("could not save state:", err)

