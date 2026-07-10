# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for cross-runtime ``env_util`` helpers."""

import os
import unittest

import _env  # noqa: F401
import env_util


class TestEnvBool(unittest.TestCase):
    def test_missing_returns_default(self):
        os.environ.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        env_util._overrides.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        self.assertFalse(env_util.env_bool("PYDISPLAY_TEST_ENV_BOOL", False))
        self.assertTrue(env_util.env_bool("PYDISPLAY_TEST_ENV_BOOL", True))

    def test_truthy_values(self):
        for value in ("1", "true", "TRUE", " yes ", "on"):
            os.environ["PYDISPLAY_TEST_ENV_BOOL"] = value
            self.assertTrue(env_util.env_bool("PYDISPLAY_TEST_ENV_BOOL", False))

    def test_falsey_values(self):
        for value in ("0", "false", "NO", " off "):
            os.environ["PYDISPLAY_TEST_ENV_BOOL"] = value
            self.assertFalse(env_util.env_bool("PYDISPLAY_TEST_ENV_BOOL", True))

    def test_unknown_value_uses_default(self):
        os.environ["PYDISPLAY_TEST_ENV_BOOL"] = "maybe"
        self.assertFalse(env_util.env_bool("PYDISPLAY_TEST_ENV_BOOL", False))
        self.assertTrue(env_util.env_bool("PYDISPLAY_TEST_ENV_BOOL", True))

    def test_env_set_override_without_os_environ(self):
        env_util._overrides.pop("PYDISPLAY_TEST_ENV_SET", None)
        os.environ.pop("PYDISPLAY_TEST_ENV_SET", None)
        env_util.env_set("PYDISPLAY_TEST_ENV_SET", "1")
        self.assertTrue(env_util.env_bool("PYDISPLAY_TEST_ENV_SET", False))
        env_util.env_set("PYDISPLAY_TEST_ENV_SET", "0")
        self.assertFalse(env_util.env_bool("PYDISPLAY_TEST_ENV_SET", True))

    def tearDown(self):
        os.environ.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        os.environ.pop("PYDISPLAY_TEST_ENV_SET", None)
        env_util._overrides.pop("PYDISPLAY_TEST_ENV_BOOL", None)
        env_util._overrides.pop("PYDISPLAY_TEST_ENV_SET", None)


if __name__ == "__main__":
    unittest.main()
