# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the ``keys`` module and displaysys DOM key helpers."""

import unittest

import _env  # noqa: F401

from displaysys._domkeys import key_to_keycode
import keys


class TestKeyTables(unittest.TestCase):
    def test_keyname_known(self):
        self.assertEqual(keys.keyname(keys.K_a), "A")
        self.assertEqual(keys.keyname(keys.K_RETURN), "Return")
        self.assertEqual(keys.keyname(keys.K_F1), "F1")

    def test_keyname_unknown_falls_back(self):
        self.assertEqual(keys.keyname(0x7FFFFFFF), "Unknown")

    def test_key_lookup_by_name(self):
        self.assertEqual(keys.key("A"), keys.K_a)
        self.assertEqual(keys.key("Return"), keys.K_RETURN)

    def test_keyname_key_roundtrip(self):
        self.assertEqual(keys.key(keys.keyname(keys.K_z)), keys.K_z)

    def test_modname_known(self):
        self.assertEqual(keys.modname(keys.KMOD_NONE), "None")
        self.assertEqual(keys.modname(keys.KMOD_LSHIFT), "Left Shift")

    def test_mod_lookup_by_name(self):
        self.assertEqual(keys.mod("Left Shift"), keys.KMOD_LSHIFT)

    def test_combined_modifiers(self):
        self.assertEqual(keys.KMOD_CTRL, keys.KMOD_LCTRL | keys.KMOD_RCTRL)
        self.assertEqual(keys.KMOD_SHIFT, keys.KMOD_LSHIFT | keys.KMOD_RSHIFT)

    def test_constants_are_ints(self):
        for name in ("K_a", "K_SPACE", "K_F12", "KMOD_LALT"):
            self.assertIsInstance(getattr(keys, name), int)


class TestDomNamedKeys(unittest.TestCase):
    def test_arrows_and_enter(self):
        self.assertEqual(key_to_keycode("ArrowUp"), keys.K_UP)
        self.assertEqual(key_to_keycode("Enter"), keys.K_RETURN)

    def test_tv_back_aliases_map_to_ac_back(self):
        # Why: webOS / Tizen / Chromium TV remotes — see platforms/pwa.md.
        for name in ("BrowserBack", "GoBack", "Back"):
            self.assertEqual(key_to_keycode(name), keys.K_AC_BACK, name)


if __name__ == "__main__":
    unittest.main()
