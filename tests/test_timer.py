# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the default ``multimer.Timer`` (whichever backend is selected)."""

import unittest

import _env  # noqa: F401
from _support import pump

import multimer
from multimer import Timer, run_queued


@unittest.skipIf(Timer is None, "no Timer backend on this platform")
class TestTimer(unittest.TestCase):
    def setUp(self):
        run_queued()
        self._timers = []

    def tearDown(self):
        for t in self._timers:
            try:
                t.deinit()
            except Exception:
                pass
        run_queued()

    def _make(self, **kwargs):
        t = Timer(-1)
        self._timers.append(t)
        if kwargs:
            t.init(**kwargs)
        return t

    def test_mode_constants(self):
        self.assertEqual(Timer.PERIODIC, 0)
        self.assertEqual(Timer.ONE_SHOT, 1)

    def test_periodic_fires_repeatedly(self):
        hits = []
        self._make(mode=Timer.PERIODIC, period=20, callback=lambda t: hits.append(1))
        pump(0.3)
        self.assertGreaterEqual(len(hits), 3)

    def test_callback_receives_timer_instance(self):
        seen = []
        t = self._make(mode=Timer.PERIODIC, period=20, callback=seen.append)
        pump(0.15)
        t.deinit()
        self.assertTrue(seen)
        self.assertIs(seen[0], t)

    def test_one_shot_fires_once(self):
        hits = []
        self._make(mode=Timer.ONE_SHOT, period=30, callback=lambda t: hits.append(1))
        pump(0.3)
        self.assertEqual(len(hits), 1)

    def test_deinit_stops_callbacks(self):
        hits = []
        t = self._make(mode=Timer.PERIODIC, period=20, callback=lambda tmr: hits.append(1))
        pump(0.1)
        t.deinit()
        count_after_deinit = len(hits)
        pump(0.2)
        self.assertEqual(len(hits), count_after_deinit)

    def test_freq_sets_period(self):
        t = self._make()
        t.init(mode=Timer.PERIODIC, freq=50, callback=lambda tmr: None)
        # 50 Hz -> 20 ms period
        self.assertEqual(t._interval, 20)

    def test_invalid_mode_raises(self):
        t = self._make()
        with self.assertRaises(ValueError):
            t.init(mode=99, period=10, callback=lambda tmr: None)

    def test_invalid_period_raises(self):
        t = self._make()
        with self.assertRaises(ValueError):
            t.init(mode=Timer.PERIODIC, period=0, callback=lambda tmr: None)


if __name__ == "__main__":
    unittest.main()
