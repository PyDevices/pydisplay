# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for displaysys quit lifecycle and backend isolation."""

import sys
import unittest
from unittest import mock

import _env  # noqa: F401
from _support import make_fbdisplay, quiet

from displaysys import DisplayDriver, default_quit_chord
from displaysys.fbdisplay import FBDisplay
from eventsys.keys import Keys


class CountingDriver(DisplayDriver):
    def __init__(self):
        self._width = 4
        self._height = 4
        self._rotation = 0
        self._requires_byteswap = False
        self.deinit_count = 0
        super().__init__(auto_refresh=False)

    def init(self):
        pass

    def fill_rect(self, x, y, w, h, c):
        return (x, y, w, h)

    def blit_rect(self, buf, x, y, w, h):
        return (x, y, w, h)

    def _deinit(self):
        self.deinit_count += 1


class TestQuitLifecycle(unittest.TestCase):
    def test_quit_calls_deinit_only(self):
        with quiet():
            d = CountingDriver()
        with mock.patch("os._exit") as exit_fn:
            d.quit()
            exit_fn.assert_not_called()
        self.assertEqual(d.deinit_count, 1)

    def test_force_quit_raises_system_exit(self):
        with quiet():
            d = CountingDriver()
        with self.assertRaises(SystemExit):
            d.force_quit(0)
        self.assertEqual(d.deinit_count, 1)

    def test_fb_inherits_quit(self):
        d, _ = make_fbdisplay(4, 4)
        with mock.patch("os._exit") as exit_fn:
            d.quit()
            exit_fn.assert_not_called()
        self.assertTrue(d._deinitialized)


class TestBackendIsolation(unittest.TestCase):
    def test_fbdisplay_does_not_import_siblings(self):
        before = set(sys.modules)

        for name in (
            "displaysys.pgdisplay",
            "displaysys.sdldisplay",
            "displaysys.psdisplay",
            "displaysys.jndisplay",
        ):
            if name not in before:
                self.assertNotIn(name, sys.modules)


class TestEventBackendDefaults(unittest.TestCase):
    def test_default_quit_chord_is_ctrl_q(self):
        self.assertEqual(default_quit_chord(), (Keys.K_q, Keys.KMOD_CTRL))


if __name__ == "__main__":
    unittest.main()
