# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the ``graphics.Draw`` convenience wrapper.

``Draw`` binds a canvas once and forwards each call to ``graphics._shapes`` /
``graphics._font``, returning the ``Area`` bounding box.
"""

import unittest

import _env  # noqa: F401
from _support import count_set, make_fb

from graphics import Area, Draw

_WHITE = 0xFFFF


class TestDraw(unittest.TestCase):
    def setUp(self):
        self.canvas = make_fb(w=16, h=16)
        self.canvas.fill(0)
        self.draw = Draw(self.canvas)

    def test_binds_canvas(self):
        self.assertIs(self.draw.canvas, self.canvas)

    def test_fill(self):
        self.assertEqual(self.draw.fill(_WHITE), Area(0, 0, 16, 16))
        self.assertEqual(count_set(self.canvas), 16 * 16)

    def test_fill_rect(self):
        self.assertEqual(self.draw.fill_rect(2, 2, 3, 3, _WHITE), Area(2, 2, 3, 3))
        self.assertEqual(count_set(self.canvas), 9)

    def test_pixel(self):
        self.assertEqual(self.draw.pixel(4, 5, _WHITE), Area(4, 5, 1, 1))
        self.assertEqual(self.canvas.pixel(4, 5), _WHITE)

    def test_hline(self):
        self.assertEqual(self.draw.hline(0, 0, 4, _WHITE), Area(0, 0, 4, 1))

    def test_rect(self):
        self.assertEqual(self.draw.rect(1, 1, 5, 5, _WHITE), Area(1, 1, 5, 5))

    def test_circle(self):
        self.assertEqual(self.draw.circle(8, 8, 3, _WHITE), Area(5, 5, 6, 6))
        self.assertGreater(count_set(self.canvas), 0)

    def test_line(self):
        self.assertIsInstance(self.draw.line(0, 0, 5, 5, _WHITE), Area)

    def test_text(self):
        self.assertIsInstance(self.draw.text("Hi", 0, 0, _WHITE), Area)
        self.assertGreater(count_set(self.canvas), 0)

    def test_blit_transparent(self):
        buf = bytearray(2 * 2 * 2)
        buf[0:2] = (0xFF, 0xFF)
        buf[2:4] = (0x00, 0x00)
        area = self.draw.blit_transparent(buf, 0, 0, 2, 2, key=0)
        self.assertEqual(area, Area(0, 0, 2, 2))

    def test_clip_fill_rect(self):
        with self.draw.clip(2, 2, 4, 4):
            self.draw.fill_rect(0, 0, 16, 16, _WHITE)
        self.assertEqual(self.canvas.pixel(1, 1), 0)
        self.assertEqual(self.canvas.pixel(2, 2), _WHITE)
        self.assertEqual(self.canvas.pixel(5, 5), _WHITE)
        self.assertEqual(self.canvas.pixel(6, 6), 0)

    def test_clip_pixel_outside_is_noop(self):
        with self.draw.clip(4, 4, 2, 2):
            self.draw.pixel(0, 0, _WHITE)
            self.draw.pixel(4, 4, _WHITE)
        self.assertEqual(self.canvas.pixel(0, 0), 0)
        self.assertEqual(self.canvas.pixel(4, 4), _WHITE)

    def test_nested_clip_intersects(self):
        with self.draw.clip(0, 0, 8, 8), self.draw.clip(4, 4, 8, 8):
            self.draw.fill_rect(0, 0, 16, 16, _WHITE)
        self.assertEqual(self.canvas.pixel(3, 3), 0)
        self.assertEqual(self.canvas.pixel(4, 4), _WHITE)
        self.assertEqual(self.canvas.pixel(7, 7), _WHITE)
        self.assertEqual(self.canvas.pixel(8, 8), 0)

    def test_clip_restored_after_context(self):
        with self.draw.clip(2, 2, 2, 2):
            self.draw.fill_rect(2, 2, 2, 2, _WHITE)
        self.draw.pixel(0, 0, _WHITE)
        self.assertEqual(self.canvas.pixel(0, 0), _WHITE)

    def test_clip_fill_only_region(self):
        self.canvas.fill(0)
        with self.draw.clip(1, 1, 3, 3):
            self.draw.fill(_WHITE)
        self.assertEqual(self.canvas.pixel(0, 0), 0)
        self.assertEqual(self.canvas.pixel(2, 2), _WHITE)
        self.assertEqual(self.canvas.pixel(4, 4), 0)

    def test_clip_accepts_area(self):
        with self.draw.clip(Area(2, 2, 2, 2)):
            self.draw.fill_rect(0, 0, 16, 16, _WHITE)
        self.assertEqual(self.canvas.pixel(2, 2), _WHITE)
        self.assertEqual(self.canvas.pixel(4, 4), 0)


if __name__ == "__main__":
    unittest.main()
