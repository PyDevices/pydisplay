# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for displaysys needs_refresh flags."""

import importlib.util
import os
import unittest

import _env  # noqa: F401
from _env import DISPLAYSYS_DIR

# pygame (pygame-ce) is only installed on Windows; unix uses SDL2. Tests that
# import PGDisplay must skip gracefully when pygame is unavailable.
HAS_PYGAME = importlib.util.find_spec("pygame") is not None


def _module_sets_needs_refresh(module_name):
    path = os.path.join(DISPLAYSYS_DIR, f"{module_name}.py")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if "needs_refresh = True" in text:
        return True
    if "needs_refresh = False" in text:
        return False
    return None


class TestNeedsRefresh(unittest.TestCase):
    def test_hosted_backends_need_refresh(self):
        from displaysys import DisplayDriver

        self.assertFalse(DisplayDriver.needs_refresh)

        for module_name in ("sdldisplay", "pgdisplay", "jndisplay", "psdisplay"):
            self.assertTrue(
                _module_sets_needs_refresh(module_name),
                module_name,
            )

        if HAS_PYGAME:
            from displaysys.pgdisplay import PGDisplay

            self.assertTrue(PGDisplay.needs_refresh)

    def test_mcu_backends_default_false(self):
        from displaysys import DisplayDriver

        self.assertFalse(DisplayDriver.needs_refresh)

        for module_name in ("busdisplay", "fbdisplay", "epaperdisplay", "pixeldisplay"):
            flag = _module_sets_needs_refresh(module_name)
            self.assertIn(flag, (None, False), module_name)


if __name__ == "__main__":
    unittest.main()
