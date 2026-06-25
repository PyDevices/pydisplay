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

    def test_blit_transparent_typo_alias_exists(self):
        # The historical misspelling is intentionally preserved.
        self.assertTrue(hasattr(self.draw, "blit_tranparent"))


if __name__ == "__main__":
    unittest.main()
