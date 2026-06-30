# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for JNDisplay vertical scroll compositing."""

import importlib.util
import unittest
from unittest import mock

import _env  # noqa: F401

from displaysys import capabilities


def _has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


HAS_JNDisplay = _has("IPython") and _has("PIL")

if HAS_JNDisplay:
    from displaysys.jndisplay import JNDisplay


@unittest.skipUnless(HAS_JNDisplay, "IPython and Pillow required for jndisplay tests")
class TestJNDisplayScroll(unittest.TestCase):
    def _make_display(self, w=10, h=12):
        fake_timer = mock.Mock()
        fake_timer.deinit = mock.Mock()
        with mock.patch("multimer.periodic", return_value=fake_timer), mock.patch.object(
            JNDisplay, "init", lambda self: None
        ):
            d = JNDisplay(w, h)
        d._timer = None
        d._jn_devices = None
        d._deinitialized = False
        d._quiet = True
        super(JNDisplay, d).vscrdef(2, h - 4, 2)
        d.vscsad(False)
        return d

    def test_capabilities_scroll_emulation(self):
        self.assertTrue(capabilities()["modules"]["jndisplay"]["scroll_emulation"])

    def test_no_scroll_render_returns_buffer(self):
        d = self._make_display()
        self.assertIs(d.render(), d._buffer)

    def test_scroll_maps_pixel(self):
        d = self._make_display()
        d._buffer.putpixel((0, 5), (255, 0, 0))
        d.vscsad(5)
        vis = d.render()
        self.assertEqual(vis.getpixel((0, 2)), (255, 0, 0))

    def test_fill_rect_updates_composite(self):
        d = self._make_display()
        d.vscsad(5)
        d.fill_rect(0, 5, 1, 1, 0xF800)
        vis = d.render()
        self.assertGreater(vis.getpixel((0, 2))[0], 200)


if __name__ == "__main__":
    unittest.main()
