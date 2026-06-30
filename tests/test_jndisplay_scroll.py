# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for JNDisplay vertical scroll compositing."""

import sys
import unittest
from unittest import mock

import _env  # noqa: F401

if "IPython" not in sys.modules:
    _ipy = mock.MagicMock()
    sys.modules["IPython"] = _ipy
    sys.modules["IPython.display"] = _ipy.display

if "PIL" not in sys.modules:
    _pil = mock.MagicMock()
    sys.modules["PIL"] = _pil
    sys.modules["PIL.Image"] = _pil.Image
    sys.modules["PIL.ImageDraw"] = _pil.ImageDraw

from displaysys import capabilities
from displaysys.jndisplay import JNDisplay


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
