# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for cross-runtime ``displaydev`` env helpers."""

import os
import unittest

import _env  # noqa: F401

import displaydev


class TestEnvBool(unittest.TestCase):
    def test_missing_returns_default(self):
        os.environ.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        displaydev._overrides.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        self.assertFalse(displaydev.env_bool("PYDISPLAY_TEST_ENV_BOOL", False))
        self.assertTrue(displaydev.env_bool("PYDISPLAY_TEST_ENV_BOOL", True))

    def test_truthy_values(self):
        for value in ("1", "true", "TRUE", " yes ", "on"):
            os.environ["PYDISPLAY_TEST_ENV_BOOL"] = value
            self.assertTrue(displaydev.env_bool("PYDISPLAY_TEST_ENV_BOOL", False))

    def test_falsey_values(self):
        for value in ("0", "false", "NO", " off "):
            os.environ["PYDISPLAY_TEST_ENV_BOOL"] = value
            self.assertFalse(displaydev.env_bool("PYDISPLAY_TEST_ENV_BOOL", True))

    def test_unknown_value_uses_default(self):
        os.environ["PYDISPLAY_TEST_ENV_BOOL"] = "maybe"
        self.assertFalse(displaydev.env_bool("PYDISPLAY_TEST_ENV_BOOL", False))
        self.assertTrue(displaydev.env_bool("PYDISPLAY_TEST_ENV_BOOL", True))

    def test_env_set_override_without_os_environ(self):
        displaydev._overrides.pop("PYDISPLAY_TEST_ENV_SET", None)
        os.environ.pop("PYDISPLAY_TEST_ENV_SET", None)
        displaydev.env_set("PYDISPLAY_TEST_ENV_SET", "1")
        self.assertTrue(displaydev.env_bool("PYDISPLAY_TEST_ENV_SET", False))
        displaydev.env_set("PYDISPLAY_TEST_ENV_SET", "0")
        self.assertFalse(displaydev.env_bool("PYDISPLAY_TEST_ENV_SET", True))

    def test_env_float(self):
        displaydev.env_set("PYDISPLAY_TEST_ENV_FLOAT", "1.25")
        self.assertEqual(displaydev.env_float("PYDISPLAY_TEST_ENV_FLOAT", 2), 1.25)
        displaydev.env_set("PYDISPLAY_TEST_ENV_FLOAT", "invalid")
        self.assertEqual(displaydev.env_float("PYDISPLAY_TEST_ENV_FLOAT", 2), 2.0)

    def tearDown(self):
        os.environ.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        os.environ.pop("PYDISPLAY_TEST_ENV_SET", None)
        displaydev._overrides.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        displaydev._overrides.pop("PYDISPLAY_TEST_ENV_FLOAT", None)
        displaydev._overrides.pop("PYDISPLAY_TEST_ENV_SET", None)


if __name__ == "__main__":
    unittest.main()
