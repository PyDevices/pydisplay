# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for runtime-owned display auto-refresh."""

import time
import unittest

import _env  # noqa: F401

from eventsys import Runtime
from multimer import sleep_ms


class _FakeDisplay:
    needs_refresh = True

    def __init__(self):
        self.shows = 0
        self.last_arg = "unset"
        self.quitted = False

    def show(self, timer=None):
        self.shows += 1
        self.last_arg = timer

    def quit(self):
        self.quitted = True


def _wait(predicate, timeout_s=1.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        sleep_ms(5)
    return predicate()


class TestRuntimeOwnedRefresh(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime()

    def tearDown(self):
        self.runtime.stop_timer()

    def test_on_tick_starts_shared_timer(self):
        self.assertIsNone(self.runtime._timer)
        hits = []
        self.runtime.on_tick(hits.append, period=20)
        self.assertIsNotNone(self.runtime._timer)
        self.assertTrue(_wait(lambda: len(hits) > 0), "shared timer never fired")

    def test_constructor_wires_refresh(self):
        display = _FakeDisplay()
        runtime = Runtime(display=display)
        self.addCleanup(runtime.stop_timer)
        self.assertTrue(_wait(lambda: display.shows > 0), "display.show never called")

    def test_subscription_deinit_unsubscribes(self):
        hits = []
        sub = self.runtime.on_tick(hits.append, period=20)
        self.assertTrue(_wait(lambda: len(hits) > 0))
        sub.deinit()
        count = len(hits)
        sleep_ms(80)
        self.assertEqual(len(hits), count)

    def test_stop_timer_clears_everything(self):
        self.runtime.on_tick(lambda t: None, period=20)
        self.assertIsNotNone(self.runtime._timer)
        self.runtime.stop_timer()
        self.assertIsNone(self.runtime._timer)
        self.assertEqual(self.runtime._tick_callbacks, [])


if __name__ == "__main__":
    unittest.main()
