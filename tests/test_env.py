# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for cross-runtime ``displaysys`` env helpers."""

import os
import unittest

import _env  # noqa: F401

import displaysys


class TestEnvBool(unittest.TestCase):
    def test_missing_returns_default(self):
        os.environ.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        displaysys._overrides.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        self.assertFalse(displaysys.env_bool("PYDISPLAY_TEST_ENV_BOOL", False))
        self.assertTrue(displaysys.env_bool("PYDISPLAY_TEST_ENV_BOOL", True))

    def test_truthy_values(self):
        for value in ("1", "true", "TRUE", " yes ", "on"):
            os.environ["PYDISPLAY_TEST_ENV_BOOL"] = value
            self.assertTrue(displaysys.env_bool("PYDISPLAY_TEST_ENV_BOOL", False))

    def test_falsey_values(self):
        for value in ("0", "false", "NO", " off "):
            os.environ["PYDISPLAY_TEST_ENV_BOOL"] = value
            self.assertFalse(displaysys.env_bool("PYDISPLAY_TEST_ENV_BOOL", True))

    def test_unknown_value_uses_default(self):
        os.environ["PYDISPLAY_TEST_ENV_BOOL"] = "maybe"
        self.assertFalse(displaysys.env_bool("PYDISPLAY_TEST_ENV_BOOL", False))
        self.assertTrue(displaysys.env_bool("PYDISPLAY_TEST_ENV_BOOL", True))

    def test_env_set_override_without_os_environ(self):
        displaysys._overrides.pop("PYDISPLAY_TEST_ENV_SET", None)
        os.environ.pop("PYDISPLAY_TEST_ENV_SET", None)
        displaysys.env_set("PYDISPLAY_TEST_ENV_SET", "1")
        self.assertTrue(displaysys.env_bool("PYDISPLAY_TEST_ENV_SET", False))
        displaysys.env_set("PYDISPLAY_TEST_ENV_SET", "0")
        self.assertFalse(displaysys.env_bool("PYDISPLAY_TEST_ENV_SET", True))

    def test_env_float(self):
        displaysys.env_set("PYDISPLAY_TEST_ENV_FLOAT", "1.25")
        self.assertEqual(displaysys.env_float("PYDISPLAY_TEST_ENV_FLOAT", 2), 1.25)
        displaysys.env_set("PYDISPLAY_TEST_ENV_FLOAT", "invalid")
        self.assertEqual(displaysys.env_float("PYDISPLAY_TEST_ENV_FLOAT", 2), 2.0)

    def tearDown(self):
        os.environ.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        os.environ.pop("PYDISPLAY_TEST_ENV_SET", None)
        displaysys._overrides.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        displaysys._overrides.pop("PYDISPLAY_TEST_ENV_FLOAT", None)
        displaysys._overrides.pop("PYDISPLAY_TEST_ENV_SET", None)


if __name__ == "__main__":
    unittest.main()
