# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the ``multimer.periodic`` convenience helper."""

import sys
import unittest

import _env  # noqa: F401
from _support import pump

from multimer import Timer, periodic
from multimer import pump as drain


class TestPeriodic(unittest.TestCase):
    def setUp(self):
        drain()
        self._timers = []

    def tearDown(self):
        for t in self._timers:
            try:
                t.deinit()
            except Exception:
                pass
        drain()

    def _track(self, t):
        self._timers.append(t)
        return t

    def test_returns_running_timer_that_fires(self):
        hits = []
        self._track(periodic(lambda t: hits.append(1), period=20))
        pump(0.2)
        self.assertGreaterEqual(len(hits), 2)

    def test_callback_receives_timer_instance(self):
        seen = []
        t = self._track(periodic(seen.append, period=20))
        pump(0.15)
        self.assertTrue(seen)
        self.assertIs(seen[0], t)

    @unittest.skipIf(sys.platform == "rp2", "rp2 always uses id -1")
    def test_auto_allocates_increasing_ids(self):
        t1 = self._track(periodic(lambda t: None, period=1000))
        t2 = self._track(periodic(lambda t: None, period=1000))
        self.assertEqual(t2.id, t1.id + 1)

    def test_async_without_loop_raises(self):
        with self.assertRaises(RuntimeError):
            periodic(lambda t: None, period=20, async_=True)


if __name__ == "__main__":
    unittest.main()
