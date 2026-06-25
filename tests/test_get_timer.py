# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the ``multimer.get_timer`` convenience helper."""

import sys
import unittest

import _env  # noqa: F401
from _support import pump

import multimer
from multimer import Timer, get_timer, run_queued


@unittest.skipIf(Timer is None, "no Timer backend on this platform")
class TestGetTimer(unittest.TestCase):
    def setUp(self):
        run_queued()
        self._debug = multimer.DEBUG
        multimer.DEBUG = False  # keep test output quiet
        self._timers = []

    def tearDown(self):
        multimer.DEBUG = self._debug
        for t in self._timers:
            try:
                t.deinit()
            except Exception:
                pass
        run_queued()

    def _track(self, t):
        self._timers.append(t)
        return t

    def test_returns_running_timer_that_fires(self):
        hits = []
        self._track(get_timer(lambda t: hits.append(1), period=20, warn=False))
        pump(0.2)
        self.assertGreaterEqual(len(hits), 2)

    def test_callback_receives_timer_instance(self):
        seen = []
        t = self._track(get_timer(seen.append, period=20, warn=False))
        pump(0.15)
        self.assertTrue(seen)
        self.assertIs(seen[0], t)

    @unittest.skipIf(sys.platform == "rp2", "rp2 always uses id -1")
    def test_auto_allocates_increasing_ids(self):
        t1 = self._track(get_timer(lambda t: None, period=1000, warn=False))
        t2 = self._track(get_timer(lambda t: None, period=1000, warn=False))
        self.assertEqual(t2.id, t1.id + 1)

    def test_asynchronous_without_loop_raises(self):
        # multimer.aio.Timer.init() requires a running event loop.
        with self.assertRaises(RuntimeError):
            get_timer(lambda t: None, period=20, asynchronous=True, warn=False)


if __name__ == "__main__":
    unittest.main()
