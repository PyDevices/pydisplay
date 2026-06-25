# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for the opt-in ``multimer.aio`` asyncio timer."""

import asyncio
import unittest

import _env  # noqa: F401

from multimer.aio import Timer, run


class TestAioTimer(unittest.TestCase):
    def test_requires_run_queued_is_false(self):
        self.assertFalse(Timer.REQUIRES_RUN_QUEUED)

    def test_init_without_running_loop_raises(self):
        t = Timer(-1)
        with self.assertRaises(RuntimeError):
            t.init(mode=Timer.PERIODIC, period=20, callback=lambda tmr: None)

    def test_periodic_fires_repeatedly(self):
        hits = []

        async def main():
            t = Timer(-1)
            t.init(mode=Timer.PERIODIC, period=20, callback=lambda tmr: hits.append(1))
            await asyncio.sleep(0.25)
            t.deinit()

        asyncio.run(main())
        self.assertGreaterEqual(len(hits), 3)

    def test_one_shot_fires_once(self):
        hits = []

        async def main():
            t = Timer(-1)
            t.init(mode=Timer.ONE_SHOT, period=30, callback=lambda tmr: hits.append(1))
            await asyncio.sleep(0.25)

        asyncio.run(main())
        self.assertEqual(len(hits), 1)

    def test_callback_receives_timer_instance(self):
        seen = []

        async def main():
            t = Timer(-1)
            t.init(mode=Timer.PERIODIC, period=20, callback=seen.append)
            await asyncio.sleep(0.1)
            t.deinit()
            return t

        created = asyncio.run(main())
        self.assertTrue(seen)
        self.assertIs(seen[0], created)

    def test_deinit_stops_callbacks(self):
        hits = []

        async def main():
            t = Timer(-1)
            t.init(mode=Timer.PERIODIC, period=20, callback=lambda tmr: hits.append(1))
            await asyncio.sleep(0.1)
            t.deinit()
            count = len(hits)
            await asyncio.sleep(0.15)
            return count

        count_at_deinit = asyncio.run(main())
        self.assertEqual(len(hits), count_at_deinit)

    def test_run_helper_runs_coroutine_to_completion(self):
        result = []

        async def main():
            await asyncio.sleep(0)
            result.append("done")

        run(main)
        self.assertEqual(result, ["done"])


if __name__ == "__main__":
    unittest.main()
