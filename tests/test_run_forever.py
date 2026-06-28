# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``multimer.run_forever`` and ``multimer.aio.run_forever``."""

import asyncio
import unittest
from unittest import mock

import _env  # noqa: F401

try:
    import multimer
    from multimer import run_forever
    from multimer.aio import run_forever as aio_run_forever

    _HAVE_MULTIMER = True
except ImportError:
    _HAVE_MULTIMER = False


@unittest.skipUnless(_HAVE_MULTIMER, "multimer not available")
class TestRunForever(unittest.TestCase):
    def test_sync_run_forever(self):
        poll_count = 0

        def poll():
            nonlocal poll_count
            poll_count += 1
            if poll_count >= 3:
                raise SystemExit

        with mock.patch.object(multimer, "run_queued") as run_queued, mock.patch.object(
            multimer, "sleep_ms"
        ) as sleep_ms, self.assertRaises(SystemExit):
            run_forever(poll, delay_ms=1)

        self.assertEqual(run_queued.call_count, 3)
        self.assertEqual(sleep_ms.call_count, 2)
        sleep_ms.assert_called_with(1)

    def test_sync_run_forever_without_poll(self):
        iterations = 0

        def stop_after_two(*_args, **_kwargs):
            nonlocal iterations
            iterations += 1
            if iterations >= 2:
                raise SystemExit

        with mock.patch.object(
            multimer, "run_queued", side_effect=stop_after_two
        ), mock.patch.object(multimer, "sleep_ms"), self.assertRaises(SystemExit):
            run_forever(delay_ms=5)

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
                "multimer.aio._sleep_ms", side_effect=instant_sleep
            ), self.assertRaises(SystemExit):
                await aio_run_forever(poll, delay_ms=1)

        asyncio.run(drive())
        self.assertEqual(poll_count, 3)

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
                "multimer.aio._sleep_ms", side_effect=instant_sleep
            ), self.assertRaises(SystemExit):
                await aio_run_forever(poll, delay_ms=1)

        asyncio.run(drive())
        self.assertEqual(poll_count, 2)


if __name__ == "__main__":
    unittest.main()
