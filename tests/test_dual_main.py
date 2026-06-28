# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``multimer.aio.dual_main``."""

import asyncio
import unittest
from unittest import mock

import _env  # noqa: F401

from multimer.aio import dual_main


class TestDualMain(unittest.TestCase):
    def test_sync_mode_calls_sync_main(self):
        ran = []
        with mock.patch("multimer.aio.run") as run:
            dual_main(lambda: ran.append(1), lambda: None, async_mode=False)
        run.assert_not_called()
        self.assertEqual(ran, [1])

    def test_async_mode_calls_run(self):
        async def async_main():
            return None

        with mock.patch("multimer.aio.run") as run:
            dual_main(lambda: None, async_main, async_mode=True)
        run.assert_called_once_with(async_main)


if __name__ == "__main__":
    unittest.main()
