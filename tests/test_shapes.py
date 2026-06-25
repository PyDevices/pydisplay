# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the module-level drawing primitives in ``graphics._shapes``.

These are the functions re-exported from the package top level (``hline``,
``rect``, ``circle`` ...). They take the canvas as the first argument and
return an :class:`graphics.Area` bounding box.
"""

from array import array
import unittest

import _env  # noqa: F401
from _support import count_set, make_fb

from graphics import (
    Area,
    arc,
    blit,
    circle,
    ellipse,
    fill,
    fill_rect,
    gradient_rect,
    hline,
    line,
    pixel,
    poly,
    polygon,
    rect,
    round_rect,
    triangle,
    vline,
)

_WHITE = 0xFFFF


class TestPrimitiveLines(unittest.TestCase):
    def setUp(self):
        self.c = make_fb(w=16, h=16)
        self.c.fill(0)

    def test_pixel(self):
        self.assertEqual(pixel(self.c, 3, 4, _WHITE), Area(3, 4, 1, 1))
        self.assertEqual(self.c.pixel(3, 4), _WHITE)

    def test_hline(self):
        self.assertEqual(hline(self.c, 1, 2, 5, _WHITE), Area(1, 2, 5, 1))
        self.assertTrue(all(self.c.pixel(x, 2) == _WHITE for x in range(1, 6)))
        self.assertEqual(self.c.pixel(6, 2), 0)

    def test_vline(self):
        self.assertEqual(vline(self.c, 1, 2, 5, _WHITE), Area(1, 2, 1, 5))
        self.assertTrue(all(self.c.pixel(1, y) == _WHITE for y in range(2, 7)))

    def test_line_diagonal_marks_endpoints(self):
        bbox = line(self.c, 0, 0, 5, 5, _WHITE)
        self.assertIsInstance(bbox, Area)
        self.assertEqual(self.c.pixel(0, 0), _WHITE)
        self.assertEqual(self.c.pixel(5, 5), _WHITE)


class TestFilledShapes(unittest.TestCase):
    def setUp(self):
        self.c = make_fb(w=16, h=16)
        self.c.fill(0)

    def test_fill(self):
        self.assertEqual(fill(self.c, _WHITE), Area(0, 0, 16, 16))
        self.assertEqual(count_set(self.c), 16 * 16)

    def test_fill_rect(self):
        self.assertEqual(fill_rect(self.c, 2, 2, 3, 3, _WHITE), Area(2, 2, 3, 3))
        self.assertEqual(count_set(self.c), 9)

    def test_rect_outline_vs_fill(self):
        self.assertEqual(rect(self.c, 1, 1, 6, 6, _WHITE), Area(1, 1, 6, 6))
        outline = count_set(self.c)
        self.c.fill(0)
        rect(self.c, 1, 1, 6, 6, _WHITE, True)
        filled = count_set(self.c)
        self.assertGreater(filled, outline)
        self.assertEqual(filled, 36)

    def test_round_rect_zero_radius_is_rect(self):
        self.assertEqual(round_rect(self.c, 0, 0, 10, 8, 0, _WHITE), Area(0, 0, 10, 8))


class TestCurves(unittest.TestCase):
    def setUp(self):
        self.c = make_fb(w=32, h=32)
        self.c.fill(0)

    def test_circle_bbox_and_draws(self):
        self.assertEqual(circle(self.c, 16, 16, 5, _WHITE), Area(11, 11, 10, 10))
        self.assertGreater(count_set(self.c), 0)

    def test_ellipse_returns_area(self):
        self.assertIsInstance(ellipse(self.c, 16, 16, 6, 4, _WHITE), Area)
        self.assertGreater(count_set(self.c), 0)

    def test_arc_returns_area(self):
        self.assertIsInstance(arc(self.c, 16, 16, 6, 0, 90, _WHITE), Area)


class TestPolygons(unittest.TestCase):
    def setUp(self):
        self.c = make_fb(w=16, h=16)
        self.c.fill(0)

    def test_triangle_outline_and_fill(self):
        self.assertIsInstance(triangle(self.c, 0, 0, 8, 0, 4, 6, _WHITE), Area)
        outline = count_set(self.c)
        self.c.fill(0)
        triangle(self.c, 0, 0, 8, 0, 4, 6, _WHITE, True)
        self.assertGreater(count_set(self.c), outline)

    def test_poly_with_point_list(self):
        bbox = poly(self.c, 0, 0, [(0, 0), (8, 0), (4, 6)], _WHITE)
        self.assertEqual(bbox, Area(0, 0, 8, 6))
        self.assertGreater(count_set(self.c), 0)

    def test_poly_requires_three_vertices(self):
        with self.assertRaises(ValueError):
            poly(self.c, 0, 0, [(0, 0), (1, 1)], _WHITE)

    def test_poly_flat_array_must_be_even(self):
        with self.assertRaises(ValueError):
            poly(self.c, 0, 0, array("h", [0, 0, 1, 1, 2]), _WHITE)

    def test_polygon_requires_three_points(self):
        with self.assertRaises(ValueError):
            polygon(self.c, [(0, 0), (1, 1)], 0, 0, _WHITE)

    def test_polygon_returns_area(self):
        self.assertEqual(
            polygon(self.c, [(0, 0), (8, 0), (4, 6)], 0, 0, _WHITE),
            Area(0, 0, 8, 6),
        )


class TestGradientAndBlit(unittest.TestCase):
    def test_gradient_without_second_color_is_solid_fill(self):
        c = make_fb(w=8, h=8)
        c.fill(0)
        self.assertEqual(gradient_rect(c, 0, 0, 8, 8, 0x1234), Area(0, 0, 8, 8))
        self.assertEqual(c.pixel(0, 0), 0x1234)
        self.assertEqual(c.pixel(7, 7), 0x1234)

    def test_vertical_gradient_changes_down_the_rows(self):
        c = make_fb(w=8, h=8)
        c.fill(0)
        gradient_rect(c, 0, 0, 8, 8, 0x0000, 0xFFFF, vertical=True)
        self.assertEqual(c.pixel(0, 0), 0)
        self.assertNotEqual(c.pixel(0, 7), 0)

    def test_blit_copies_pixels(self):
        src = make_fb(w=4, h=4)
        src.fill(0xABCD)
        dst = make_fb(w=16, h=16)
        dst.fill(0)
        self.assertEqual(blit(dst, src, 2, 2), Area(2, 2, 4, 4))
        self.assertEqual(dst.pixel(2, 2), 0xABCD)
        self.assertEqual(dst.pixel(0, 0), 0)

    def test_blit_fully_out_of_bounds_is_noop(self):
        src = make_fb(w=4, h=4)
        src.fill(0xABCD)
        dst = make_fb(w=16, h=16)
        dst.fill(0)
        self.assertIsNone(blit(dst, src, 100, 100))
        self.assertEqual(count_set(dst), 0)


if __name__ == "__main__":
    unittest.main()
