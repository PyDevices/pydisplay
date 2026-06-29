# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``eventsys.capabilities()``."""

import unittest

import _env  # noqa: F401

import eventsys


class TestCapabilities(unittest.TestCase):
    def test_capabilities_snapshot(self):
        caps = eventsys.capabilities()
        self.assertIn("dialect", caps)
        self.assertIn("devices", caps)
        self.assertIn("joystick", caps)
        self.assertTrue(caps["joystick"])
        self.assertIn("joystick", caps["devices"])


if __name__ == "__main__":
    unittest.main()
