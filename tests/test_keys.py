# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the ``eventsys.keys`` key/modifier tables and helpers."""

import unittest

import _env  # noqa: F401

from eventsys.keys import Keys, key_to_keycode


class TestKeyTables(unittest.TestCase):
    def test_keyname_known(self):
        self.assertEqual(Keys.keyname(Keys.K_a), "A")
        self.assertEqual(Keys.keyname(Keys.K_RETURN), "Return")
        self.assertEqual(Keys.keyname(Keys.K_F1), "F1")

    def test_keyname_unknown_falls_back(self):
        self.assertEqual(Keys.keyname(0x7FFFFFFF), "Unknown")

    def test_key_lookup_by_name(self):
        self.assertEqual(Keys.key("A"), Keys.K_a)
        self.assertEqual(Keys.key("Return"), Keys.K_RETURN)

    def test_keyname_key_roundtrip(self):
        self.assertEqual(Keys.key(Keys.keyname(Keys.K_z)), Keys.K_z)

    def test_modname_known(self):
        self.assertEqual(Keys.modname(Keys.KMOD_NONE), "None")
        self.assertEqual(Keys.modname(Keys.KMOD_LSHIFT), "Left Shift")

    def test_mod_lookup_by_name(self):
        self.assertEqual(Keys.mod("Left Shift"), Keys.KMOD_LSHIFT)

    def test_combined_modifiers(self):
        self.assertEqual(Keys.KMOD_CTRL, Keys.KMOD_LCTRL | Keys.KMOD_RCTRL)
        self.assertEqual(Keys.KMOD_SHIFT, Keys.KMOD_LSHIFT | Keys.KMOD_RSHIFT)

    def test_constants_are_ints(self):
        for name in ("K_a", "K_SPACE", "K_F12", "KMOD_LALT"):
            self.assertIsInstance(getattr(Keys, name), int)


class TestDomNamedKeys(unittest.TestCase):
    def test_arrows_and_enter(self):
        self.assertEqual(key_to_keycode("ArrowUp"), Keys.K_UP)
        self.assertEqual(key_to_keycode("Enter"), Keys.K_RETURN)

    def test_tv_back_aliases_map_to_ac_back(self):
        # Why: webOS / Tizen / Chromium TV remotes — see platforms/pwa.md.
        for name in ("BrowserBack", "GoBack", "Back"):
            self.assertEqual(key_to_keycode(name), Keys.K_AC_BACK, name)


if __name__ == "__main__":
    unittest.main()
