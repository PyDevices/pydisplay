# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``multimer.run_forever`` and ``multimer.run_forever_async``."""

import asyncio
import unittest
from unittest import mock

import _env  # noqa: F401

import multimer
from multimer import run_forever, run_forever_async


class TestRunForever(unittest.TestCase):
    def test_sync_run_forever(self):
        poll_count = 0

        def poll():
            nonlocal poll_count
            poll_count += 1
            if poll_count >= 3:
                raise SystemExit

        with mock.patch.object(multimer, "pump") as pump_fn, mock.patch(
            "multimer._sync_sleep_ms"
        ) as sleep_ms, self.assertRaises(SystemExit):
            run_forever(poll, delay_ms=1)

        self.assertEqual(pump_fn.call_count, 3)
        self.assertEqual(sleep_ms.call_count, 2)
        sleep_ms.assert_called_with(1)

    def test_sync_run_forever_without_poll(self):
        iterations = 0

        def stop_after_two(*_args, **_kwargs):
            nonlocal iterations
            iterations += 1
            if iterations >= 2:
                raise SystemExit

        with mock.patch.object(multimer, "pump", side_effect=stop_after_two), mock.patch(
            "multimer._sync_sleep_ms"
        ), self.assertRaises(SystemExit):
            run_forever(delay_ms=5)

    @unittest.skipIf(run_forever_async is None, "async support not available")
    def test_aio_run_forever_sync_poll(self):
        poll_count = 0

        def poll():
            nonlocal poll_count
            poll_count += 1
            if poll_count >= 3:
                raise SystemExit

        async def instant_sleep(_ms):
            return None

        async def drive():
            with mock.patch(
                "multimer._async.sleep_ms", side_effect=instant_sleep
            ), self.assertRaises(SystemExit):
                await run_forever_async(poll, delay_ms=1)

        asyncio.run(drive())
        self.assertEqual(poll_count, 3)

    @unittest.skipIf(run_forever_async is None, "async support not available")
    def test_aio_run_forever_async_poll(self):
        poll_count = 0

        async def poll():
            nonlocal poll_count
            poll_count += 1
            if poll_count >= 2:
                raise SystemExit

        async def instant_sleep(_ms):
            return None

        async def drive():
            with mock.patch(
                "multimer._async.sleep_ms", side_effect=instant_sleep
            ), self.assertRaises(SystemExit):
                await run_forever_async(poll, delay_ms=1)

        asyncio.run(drive())
        self.assertEqual(poll_count, 2)


if __name__ == "__main__":
    unittest.main()
