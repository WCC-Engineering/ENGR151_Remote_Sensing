"""Tests for processing.py. Owner: add tests for YOUR processing."""

import json

import kit
import processing


def run(values, dt=900):
    """Feed a list of calibrated values (data4) through process(), starting
    with fresh memory. Returns the list of Data objects. None stands for a
    failed sensor read."""
    kit.reset_memory()
    samples = []
    for i, value in enumerate(values):
        data = kit.Data(1_000_000 + i * dt)
        if value is None:
            data.ok = False
        else:
            data.data4 = value
        processing.process(data)
        samples.append(data)
    return samples


def test_smoothing_reduces_noise():
    noisy = [100 + (5 if i % 2 else -5) for i in range(30)]
    samples = run(noisy)
    assert all(abs(d.data3 - 100) < 5 for d in samples[processing.WINDOW:])


def test_event_turns_on_and_off():
    values = [100] * 20 + [100 + 50 * i for i in range(1, 15)] + [800] * 30
    flags = [d.data5 for d in run(values)]
    assert any(flags), "a fast rise should start an event"
    assert not flags[-1], "the event should end once the value stops rising"


def test_bad_reading_does_not_crash():
    samples = run([100, None, 100, 99999])
    assert samples[1].ok is False
    assert samples[3].ok is False       # out of range


def test_memory_survives_a_reboot():
    # The Pico saves the memory objects as JSON in state.json. After a reboot,
    # restore_memory() should put them back exactly.
    run([100, 110, 120, 130])
    state = {}
    kit.save_memory(state)
    saved = json.loads(json.dumps(state))     # what state.json would hold
    before = processing.smoother.average()
    kit.reset_memory()
    kit.restore_memory(saved)
    assert processing.smoother.average() == before
    assert processing.rate.last_value is not None
