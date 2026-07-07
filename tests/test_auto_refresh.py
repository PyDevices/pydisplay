# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for broker-owned display auto-refresh (migrated to the multimer API).

Display drivers no longer own a refresh timer. The broker owns one shared
``multimer`` timer and fans ticks out to subscribers via ``Broker.on_tick``.
``board_config`` wires ``broker.on_tick(display_drv.show, ...)`` so the display
refreshes periodically without the display keeping any timer reference.
"""

import time
import unittest

import _env  # noqa: F401

from eventsys import Broker
from multimer import sleep_ms


class _FakeDisplay:
    def __init__(self):
        self.shows = 0
        self.last_arg = "unset"

    def show(self, timer=None):
        self.shows += 1
        self.last_arg = timer


def _wait(predicate, timeout_s=1.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        sleep_ms(5)
    return predicate()


class TestBrokerOwnedRefresh(unittest.TestCase):
    def setUp(self):
        self.broker = Broker()

    def tearDown(self):
        self.broker.stop_timer()

    def test_on_tick_starts_shared_timer(self):
        self.assertIsNone(self.broker._timer)
        hits = []
        self.broker.on_tick(hits.append, period=20)
        self.assertIsNotNone(self.broker._timer)
        self.assertTrue(_wait(lambda: len(hits) > 0), "shared timer never fired")

    def test_refresh_calls_display_show(self):
        display = _FakeDisplay()
        self.broker.on_tick(display.show, period=20)
        self.assertTrue(_wait(lambda: display.shows > 0), "display.show never called")
        # The broker passes the timer object as show()'s positional argument.
        self.assertIsNot(display.last_arg, "unset")

    def test_subscription_deinit_unsubscribes(self):
        hits = []
        sub = self.broker.on_tick(hits.append, period=20)
        self.assertTrue(_wait(lambda: len(hits) > 0))
        sub.deinit()
        count = len(hits)
        sleep_ms(80)  # timer keeps running, but this callback must not fire again
        self.assertEqual(len(hits), count)

    def test_stop_timer_clears_everything(self):
        self.broker.on_tick(lambda t: None, period=20)
        self.assertIsNotNone(self.broker._timer)
        self.broker.stop_timer()
        self.assertIsNone(self.broker._timer)
        self.assertEqual(self.broker._tick_callbacks, [])


if __name__ == "__main__":
    unittest.main()
