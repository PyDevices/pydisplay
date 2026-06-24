# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the ``graphics.Area`` rectangle helper."""

import unittest

import _env  # noqa: F401

from graphics import Area


class TestAreaConstruction(unittest.TestCase):
    def test_positional_args(self):
        a = Area(1, 2, 3, 4)
        self.assertEqual((a.x, a.y, a.w, a.h), (1, 2, 3, 4))

    def test_tuple_arg(self):
        a = Area((5, 6, 7, 8))
        self.assertEqual((a.x, a.y, a.w, a.h), (5, 6, 7, 8))

    def test_missing_args_raises(self):
        with self.assertRaises(ValueError):
            Area(1)
        with self.assertRaises(ValueError):
            Area(1, 2)


class TestAreaContainment(unittest.TestCase):
    def setUp(self):
        self.a = Area(0, 0, 10, 10)

    def test_contains_point(self):
        self.assertTrue(self.a.contains(5, 5))
        self.assertTrue(self.a.contains(0, 0))

    def test_contains_is_half_open(self):
        # The far edges are exclusive.
        self.assertFalse(self.a.contains(10, 10))
        self.assertFalse(self.a.contains(-1, 5))

    def test_contains_tuple(self):
        self.assertTrue(self.a.contains((3, 4)))

    def test_contains_area(self):
        self.assertTrue(self.a.contains_area(Area(1, 1, 2, 2)))
        self.assertFalse(self.a.contains_area(Area(0, 0, 20, 20)))


class TestAreaOverlap(unittest.TestCase):
    def test_intersects(self):
        self.assertTrue(Area(0, 0, 5, 5).intersects(Area(4, 4, 5, 5)))

    def test_edge_touch_does_not_intersect(self):
        # Sharing only an edge is not an intersection.
        self.assertFalse(Area(0, 0, 5, 5).intersects(Area(5, 5, 2, 2)))

    def test_disjoint_does_not_intersect(self):
        self.assertFalse(Area(0, 0, 5, 5).intersects(Area(10, 10, 2, 2)))

    def test_edge_touch_counts_as_touch(self):
        self.assertTrue(Area(0, 0, 5, 5).touches_or_intersects(Area(5, 5, 2, 2)))

    def test_gap_does_not_touch(self):
        self.assertFalse(Area(0, 0, 5, 5).touches_or_intersects(Area(6, 6, 2, 2)))


class TestAreaTransforms(unittest.TestCase):
    def test_shift(self):
        self.assertEqual(Area(1, 2, 3, 4).shift(10, 20), Area(11, 22, 3, 4))

    def test_clip(self):
        self.assertEqual(Area(0, 0, 10, 10).clip(Area(5, 5, 10, 10)), Area(5, 5, 5, 5))

    def test_offset_uniform(self):
        self.assertEqual(Area(2, 2, 4, 4).offset(1), Area(1, 1, 6, 6))

    def test_offset_x_y(self):
        self.assertEqual(Area(2, 2, 4, 4).offset(1, 2), Area(1, 0, 6, 8))

    def test_inset_uniform(self):
        self.assertEqual(Area(2, 2, 4, 4).inset(1), Area(3, 3, 2, 2))

    def test_union_via_add(self):
        self.assertEqual(Area(0, 0, 2, 2) + Area(4, 4, 2, 2), Area(0, 0, 6, 6))


class TestAreaProtocols(unittest.TestCase):
    def test_eq_and_ne(self):
        self.assertEqual(Area(1, 2, 3, 4), Area(1, 2, 3, 4))
        self.assertNotEqual(Area(1, 2, 3, 4), Area(1, 2, 3, 5))

    def test_iterable_unpacks_to_xywh(self):
        x, y, w, h = Area(1, 2, 3, 4)
        self.assertEqual((x, y, w, h), (1, 2, 3, 4))

    def test_repr(self):
        self.assertEqual(repr(Area(1, 2, 3, 4)), "Area(1, 2, 3, 4)")

    def test_is_unhashable(self):
        # Area defines __eq__ but sets __hash__ = None on purpose.
        with self.assertRaises(TypeError):
            hash(Area(1, 2, 3, 4))


if __name__ == "__main__":
    unittest.main()
