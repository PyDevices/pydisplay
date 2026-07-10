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
        """``capabilities()`` must not import concrete display backends.

        Other tests may already have loaded ``pgdisplay`` / ``sdldisplay`` into
        ``sys.modules`` (especially when pygame is installed). Assert only that
        *this* call does not pull them in.
        """
        import displaysys

        before = set(sys.modules)
        _ = displaysys.capabilities()
        newly = set(sys.modules) - before
        self.assertNotIn("displaysys.pgdisplay", newly)
        self.assertNotIn("displaysys.sdldisplay", newly)


if __name__ == "__main__":
    unittest.main()
