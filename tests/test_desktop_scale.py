# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for desktop window scale fitting."""

import unittest

import _env  # noqa: F401

from displaysys import (
    _DESKTOP_SCALE_MARGIN,
    _DESKTOP_WINDOW_CHROME_H,
    desktop_work_area,
    fit_scale_to_desktop,
)


class TestFitScaleToDesktop(unittest.TestCase):
    def test_no_clamp_when_window_fits(self):
        self.assertEqual(fit_scale_to_desktop(320, 480, 2, 1920, 1200), 2)

    def test_clamp_when_too_tall(self):
        # 320x480 @ scale 2 -> 640x960; desktop 1280x752 minus margin -> max_h 704
        fitted = fit_scale_to_desktop(320, 480, 2, 1280, 752)
        self.assertAlmostEqual(fitted, 704 / 480, places=5)

    def test_unknown_desktop_leaves_scale(self):
        self.assertEqual(fit_scale_to_desktop(320, 480, 2, 0, 0), 2)

    def test_margin_applied(self):
        max_h = 752 - _DESKTOP_SCALE_MARGIN
        fitted = fit_scale_to_desktop(320, 480, 2, 1280, 752, margin=_DESKTOP_SCALE_MARGIN)
        self.assertAlmostEqual(fitted, max_h / 480, places=5)

    def test_chrome_reserved(self):
        # Usable 1280x752 (taskbar excluded); chrome reserves title bar / frame.
        max_h = 752 - _DESKTOP_SCALE_MARGIN - _DESKTOP_WINDOW_CHROME_H
        fitted = fit_scale_to_desktop(
            320,
            480,
            2,
            1280,
            752,
            chrome_w=16,
            chrome_h=_DESKTOP_WINDOW_CHROME_H,
        )
        self.assertAlmostEqual(fitted, max_h / 480, places=5)
        self.assertLess(fitted, fit_scale_to_desktop(320, 480, 2, 1280, 752))

    def test_desktop_work_area_shape(self):
        area = desktop_work_area()
        self.assertEqual(len(area), 4)
        for v in area:
            self.assertIsInstance(v, int)


if __name__ == "__main__":
    unittest.main()
