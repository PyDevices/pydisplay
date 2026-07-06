# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the ``displaysys.DisplayDriver`` base class.

Geometry, byte-swap and lifecycle behaviour are exercised through the concrete
``FBDisplay`` driver (a real subclass with no hardware needs). The vertical
scroll math is exercised through ``ScrollDisplay`` below, a minimal driver that
overrides ``vscsad`` to return the stored register value the way real hardware
drivers (e.g. ``BusDisplay``) do.
"""

import unittest

import _env  # noqa: F401
from _support import make_fbdisplay, quiet

from displaysys import DisplayDriver


class FakeTouch:
    def __init__(self):
        self.rotation = None


class ScrollDisplay(DisplayDriver):
    """Smallest driver that makes the base scroll helpers observable."""

    def __init__(self, width=10, height=10):
        self._width = width
        self._height = height
        self._rotation = 0
        self._requires_byteswap = False
        super().__init__()

    def init(self):
        # base __init__ resets _vssa to False; give it a real start value
        self._vssa = 0

    def vscsad(self, vssa=None):
        if vssa is not None:
            super().vscsad(vssa)
        return self._vssa

    def fill_rect(self, x, y, w, h, c):
        return (x, y, w, h)

    def blit_rect(self, buf, x, y, w, h):
        return (x, y, w, h)


def make_scroll(width=10, height=10, **kwargs):
    with quiet():
        return ScrollDisplay(width, height, **kwargs)


class TestGeometry(unittest.TestCase):
    def test_default_dimensions(self):
        d, _ = make_fbdisplay(8, 4)
        self.assertEqual((d.width, d.height), (8, 4))
        self.assertEqual(d.rotation, 0)

    def test_rotation_swaps_width_and_height(self):
        d, _ = make_fbdisplay(8, 4)
        with quiet():
            d.rotation = 90
        self.assertEqual((d.width, d.height), (4, 8))
        with quiet():
            d.rotation = 180
        self.assertEqual((d.width, d.height), (8, 4))

    def test_rotation_setter_scales_small_values_to_degrees(self):
        d, _ = make_fbdisplay(8, 4)
        with quiet():
            d.rotation = 1  # interpreted as index 1 -> 90 degrees
        self.assertEqual(d.rotation, 90)

    def test_rotation_no_change_is_cheap(self):
        d, _ = make_fbdisplay(8, 4)
        with quiet():
            d.rotation = 0
        self.assertEqual(d.rotation, 0)


class TestByteswapControls(unittest.TestCase):
    def test_requires_byteswap_reflects_constructor(self):
        d, _ = make_fbdisplay(reverse_bytes_in_word=False)
        self.assertFalse(d.requires_byteswap)
        d2, _ = make_fbdisplay(reverse_bytes_in_word=True)
        self.assertTrue(d2.requires_byteswap)

    def test_disable_auto_byteswap_when_supported(self):
        d, _ = make_fbdisplay(reverse_bytes_in_word=True)
        with quiet():
            disabled = d.disable_auto_byteswap(True)
        self.assertTrue(disabled)
        self.assertFalse(d._auto_byteswap)
        with quiet():
            re_enabled = d.disable_auto_byteswap(False)
        self.assertFalse(re_enabled)
        self.assertTrue(d._auto_byteswap)

    def test_disable_auto_byteswap_when_not_required(self):
        d, _ = make_fbdisplay(reverse_bytes_in_word=False)
        with quiet():
            disabled = d.disable_auto_byteswap(True)
        self.assertTrue(disabled)
        self.assertFalse(d._auto_byteswap)


class TestTouchDevice(unittest.TestCase):
    def test_valid_touch_device_inherits_rotation(self):
        d, _ = make_fbdisplay(8, 4)
        with quiet():
            d.rotation = 90
        touch = FakeTouch()
        d.touch_device = touch
        self.assertIs(d.touch_device, touch)
        self.assertEqual(touch.rotation, d.rotation)

    def test_invalid_touch_device_raises(self):
        d, _ = make_fbdisplay(8, 4)
        with self.assertRaises(ValueError):
            d.touch_device = object()


class TestPowerBrightnessDefaults(unittest.TestCase):
    def test_defaults_are_sentinels(self):
        d, _ = make_fbdisplay(8, 4)
        self.assertEqual(d.power, -1)
        self.assertEqual(d.brightness, -1)

    def test_base_setters_are_noops(self):
        d, _ = make_fbdisplay(8, 4)
        d.power = True
        d.brightness = 0.5
        # base class keeps the read-only sentinels
        self.assertEqual(d.power, -1)
        self.assertEqual(d.brightness, -1)


class TestLifecycle(unittest.TestCase):
    def test_deinit_is_idempotent(self):
        d, _ = make_fbdisplay(8, 4)
        d.deinit()
        self.assertTrue(d._deinitialized)
        d.deinit()  # second call must not raise
        self.assertTrue(d._deinitialized)


class TestScrollMath(unittest.TestCase):
    def test_set_vscroll_partitions_height(self):
        d = make_scroll(10, 10)
        d.set_vscroll(tfa=2, bfa=2)
        self.assertEqual((d.tfa, d.vsa, d.bfa), (2, 6, 2))
        self.assertEqual(d.vscroll, 0)

    def test_vscrdef_rejects_bad_partition(self):
        d = make_scroll(10, 10)
        with self.assertRaises(ValueError):
            d.vscrdef(2, 2, 2)  # 2+2+2 != 10

    def test_vscsad_normalizes_out_of_range(self):
        d = make_scroll(10, 10)
        self.assertEqual(d.vscsad(15), 5)  # wraps modulo height
        self.assertEqual(d.vscsad(-1), 9)  # wraps from below

    def test_scroll_by_and_to(self):
        d = make_scroll(10, 10)
        d.set_vscroll(tfa=2, bfa=2)
        d.scroll_by(3)
        self.assertEqual(d.vscroll, 3)
        d.scroll_to(1)
        self.assertEqual(d.vscroll, 1)

    def test_scroll_horizontal_unsupported(self):
        d = make_scroll(10, 10)
        with self.assertRaises(NotImplementedError):
            d.scroll(5, 0)

    def test_translate_point_wraps_in_scroll_area(self):
        d = make_scroll(10, 10)
        d.set_vscroll(tfa=2, bfa=2)
        d.scroll_by(3)  # vscsad -> 5
        self.assertEqual(d.translate_point((1, 5)), (1, 2))

    def test_translate_point_passthrough_when_not_scrolled(self):
        d = make_scroll(10, 10)
        self.assertEqual(d.translate_point((4, 4)), (4, 4))

    def test_scroll_areas(self):
        d = make_scroll(10, 10)
        d.set_vscroll(tfa=2, bfa=2)
        self.assertEqual(d.tfa_area, (0, 0, 10, 2))
        self.assertEqual(d.vsa_area, (0, 2, 10, 6))
        self.assertEqual(d.bfa_area, (0, 8, 10, 2))


if __name__ == "__main__":
    unittest.main()
