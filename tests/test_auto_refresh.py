# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the optional ``auto_refresh`` timer wiring in ``DisplayDriver``."""

import time
import unittest
from unittest import mock

import _env  # noqa: F401
from _support import quiet

from displaysys import DisplayDriver

try:
    import multimer

    _HAVE_MULTIMER = True
except ImportError:
    _HAVE_MULTIMER = False


class CountingDisplay(DisplayDriver):
    def __init__(self, auto_refresh=False, *, async_=False):
        self._width = 4
        self._height = 4
        self._rotation = 0
        self._requires_byteswap = False
        self.show_count = 0
        super().__init__(auto_refresh=auto_refresh, async_=async_)

    def init(self):
        self._vssa = 0

    def fill_rect(self, x, y, w, h, c):
        return (x, y, w, h)

    def blit_rect(self, buf, x, y, w, h):
        return (x, y, w, h)

    def show(self, *args, **kwargs):
        self.show_count += 1


@unittest.skipUnless(_HAVE_MULTIMER, "multimer not available")
class TestAutoRefresh(unittest.TestCase):
    def _pump(self, duration_s, step_s=0.005):
        end = time.monotonic() + duration_s
        while time.monotonic() < end:
            multimer.pump()
            time.sleep(step_s)
        multimer.pump()

    def test_no_timer_when_disabled(self):
        with quiet():
            d = CountingDisplay(auto_refresh=False)
        self.addCleanup(d.deinit)
        self.assertIsNone(d._timer)

    def test_timer_created_and_fires(self):
        with quiet():
            d = CountingDisplay(auto_refresh=20)
        self.addCleanup(d.deinit)
        self.assertIsNotNone(d._timer)
        self._pump(0.25)
        self.assertGreaterEqual(d.show_count, 2)

    def test_deinit_stops_refresh(self):
        with quiet():
            d = CountingDisplay(auto_refresh=20)
        self._pump(0.1)
        d.deinit()
        self.assertIsNone(d._timer)
        count_after_deinit = d.show_count
        self._pump(0.2)
        self.assertEqual(d.show_count, count_after_deinit)

    def test_default_uses_sync_timer(self):
        import multimer

        fake_timer = mock.Mock()
        with quiet(), mock.patch.object(
            multimer, "periodic", return_value=fake_timer
        ) as periodic_fn:
            d = CountingDisplay(auto_refresh=20)
        self.addCleanup(d.deinit)
        periodic_fn.assert_called_once()
        self.assertFalse(periodic_fn.call_args.kwargs["async_"])
        self.assertIs(d._timer, fake_timer)

    def test_explicit_async_passes_async_to_periodic(self):
        import multimer

        fake_timer = mock.Mock()
        with quiet(), mock.patch.object(
            multimer, "periodic", return_value=fake_timer
        ) as periodic_fn:
            d = CountingDisplay(auto_refresh=20, async_=True)
        self.addCleanup(d.deinit)
        periodic_fn.assert_called_once()
        self.assertTrue(periodic_fn.call_args.kwargs["async_"])
        self.assertIs(d._timer, fake_timer)


if __name__ == "__main__":
    unittest.main()
