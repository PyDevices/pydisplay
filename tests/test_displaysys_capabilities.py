# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``displaydev.capabilities()``."""

import sys
import unittest

import _env  # noqa: F401

from displaydev import capabilities


class TestDisplaydevCapabilities(unittest.TestCase):
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
            "windisplay",
            "psdisplay",
            "jndisplay",
            "auto",
        ):
            self.assertIn(name, modules)
            if name != "auto":
                self.assertIn("auto_refresh", modules[name])
        self.assertTrue(modules["auto"].get("host_select"))

    def test_no_backend_import_side_effects(self):
        """``capabilities()`` must not import concrete display backends.

        Other tests may already have loaded ``pgdisplay`` / ``sdldisplay`` into
        ``sys.modules`` (especially when pygame is installed). Assert only that
        *this* call does not pull them in.
        """
        import displaydev

        before = set(sys.modules)
        _ = displaydev.capabilities()
        newly = set(sys.modules) - before
        self.assertNotIn("displaydev.pgdisplay", newly)
        self.assertNotIn("displaydev.sdldisplay", newly)
        self.assertNotIn("displaydev.windisplay", newly)


if __name__ == "__main__":
    unittest.main()
