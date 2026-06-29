# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Backend import isolation for displaysys."""

import sys
import unittest

import _env  # noqa: F401


class TestBackendIsolation(unittest.TestCase):
    def test_busdisplay_does_not_load_other_backends(self):
        if sys.implementation.name != "micropython":
            self.skipTest("BusDisplay imports only on MicroPython")
        before = set(sys.modules)
        import displaysys.busdisplay  # noqa: F401

        for name in (
            "displaysys.fbdisplay",
            "displaysys.pgdisplay",
            "displaysys.psdisplay",
            "displaysys.jndisplay",
            "displaysys.sdldisplay",
        ):
            if name not in before:
                self.assertNotIn(name, sys.modules, f"busdisplay imported {name}")


if __name__ == "__main__":
    unittest.main()
