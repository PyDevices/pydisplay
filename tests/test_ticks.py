# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the cross-platform tick helpers in ``multimer._ticks``."""

import time
import unittest

import _env  # noqa: F401

from multimer import sleep_ms, ticks_add, ticks_diff, ticks_less, ticks_ms

_TICKS_PERIOD = 1 << 29
_TICKS_MAX = _TICKS_PERIOD - 1


class TestTicksMath(unittest.TestCase):
    def test_ticks_ms_returns_int_within_period(self):
        t = ticks_ms()
        self.assertIsInstance(t, int)
        self.assertGreaterEqual(t, 0)
        self.assertLessEqual(t, _TICKS_MAX)

    def test_ticks_add_simple(self):
        self.assertEqual(ticks_add(100, 50), 150)

    def test_ticks_add_wraps_at_period(self):
        self.assertEqual(ticks_add(_TICKS_MAX, 1), 0)
        self.assertEqual(ticks_add(0, -1), _TICKS_MAX)

    def test_ticks_add_overflow_guard(self):
        with self.assertRaises(OverflowError):
            ticks_add(0, _TICKS_PERIOD)

    def test_ticks_diff_sign(self):
        self.assertEqual(ticks_diff(150, 100), 50)
        self.assertEqual(ticks_diff(100, 150), -50)
        self.assertEqual(ticks_diff(100, 100), 0)

    def test_ticks_diff_wraparound(self):
        # later value has wrapped past the period boundary
        later = ticks_add(_TICKS_MAX, 10)  # == 9
        self.assertEqual(ticks_diff(later, _TICKS_MAX), 10)

    def test_ticks_less(self):
        self.assertTrue(ticks_less(100, 150))
        self.assertFalse(ticks_less(150, 100))
        self.assertFalse(ticks_less(100, 100))


class TestTicksTiming(unittest.TestCase):
    def test_ticks_ms_advances_over_real_sleep(self):
        start = ticks_ms()
        time.sleep(0.05)
        elapsed = ticks_diff(ticks_ms(), start)
        # generous bounds to tolerate slow/loaded CI machines
        self.assertGreaterEqual(elapsed, 30)
        self.assertLess(elapsed, 2000)

    def test_sleep_ms_blocks_at_least_requested(self):
        start = time.monotonic()
        sleep_ms(60)
        elapsed = (time.monotonic() - start) * 1000
        self.assertGreaterEqual(elapsed, 40)

    def test_sleep_ms_zero_returns_promptly(self):
        start = time.monotonic()
        sleep_ms(0)
        elapsed = (time.monotonic() - start) * 1000
        self.assertLess(elapsed, 200)


if __name__ == "__main__":
    unittest.main()
