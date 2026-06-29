# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``displaysys.capabilities()``."""

import sys
import unittest

import _env  # noqa: F401

from displaysys import capabilities


class TestDisplaysysCapabilities(unittest.TestCase):
    def test_returns_dict(self):
        caps = capabilities()
        self.assertIsInstance(caps, dict)
        self.assertEqual(caps["dialect"], sys.implementation.name)
        self.assertIn(caps["byteswap"], ("native", "pure_python"))

    def test_modules_documented(self):
        modules = capabilities()["modules"]
        for name in (
            "busdisplay",
            "fbdisplay",
            "sdldisplay",
            "pgdisplay",
            "psdisplay",
            "jndisplay",
        ):
            self.assertIn(name, modules)
            self.assertIn("auto_refresh", modules[name])

    def test_no_backend_import_side_effects(self):
        import displaysys

        self.assertNotIn("displaysys.pgdisplay", sys.modules)
        self.assertNotIn("displaysys.sdldisplay", sys.modules)
        _ = displaysys.capabilities()


if __name__ == "__main__":
    unittest.main()
