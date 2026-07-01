# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for ``multimer.AsyncTimer`` and async helpers."""

import asyncio
import unittest

import _env  # noqa: F401

from multimer import AsyncTimer, run

try:
    from multimer._mpasyncio import Event as MpEvent
    from multimer._mpasyncio import run as mp_run

    _MPASYNCIO_AVAILABLE = True
except ImportError:
    MpEvent = None
    mp_run = None
    _MPASYNCIO_AVAILABLE = False


@unittest.skipIf(AsyncTimer is None, "async support not available")
class TestAsyncTimer(unittest.TestCase):
    def test_needs_pump_is_false(self):
        self.assertFalse(AsyncTimer(-1).needs_pump)

    def test_init_without_running_loop_raises(self):
        t = AsyncTimer(-1)
        with self.assertRaises(RuntimeError):
            t.init(mode=AsyncTimer.PERIODIC, period=20, callback=lambda tmr: None)

    def test_periodic_fires_repeatedly(self):
        hits = []

        async def main():
            t = AsyncTimer(-1)
            t.init(mode=AsyncTimer.PERIODIC, period=20, callback=lambda tmr: hits.append(1))
            await asyncio.sleep(0.25)
            t.deinit()

        asyncio.run(main())
        self.assertGreaterEqual(len(hits), 3)

    def test_one_shot_fires_once(self):
        hits = []

        async def main():
            t = AsyncTimer(-1)
            t.init(mode=AsyncTimer.ONE_SHOT, period=30, callback=lambda tmr: hits.append(1))
            await asyncio.sleep(0.25)

        asyncio.run(main())
        self.assertEqual(len(hits), 1)

    def test_callback_receives_timer_instance(self):
        seen = []

        async def main():
            t = AsyncTimer(-1)
            t.init(mode=AsyncTimer.PERIODIC, period=20, callback=seen.append)
            await asyncio.sleep(0.1)
            t.deinit()
            return t

        created = asyncio.run(main())
        self.assertTrue(seen)
        self.assertIs(seen[0], created)

    def test_deinit_stops_callbacks(self):
        hits = []

        async def main():
            t = AsyncTimer(-1)
            t.init(mode=AsyncTimer.PERIODIC, period=20, callback=lambda tmr: hits.append(1))
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


@unittest.skipIf(not _MPASYNCIO_AVAILABLE, "_mpasyncio requires MicroPython _asyncio")
class TestMpAsyncioEvent(unittest.TestCase):
    def test_starts_cleared(self):
        ev = MpEvent()
        self.assertFalse(ev.is_set())

    def test_wait_until_set(self):
        seen = []

        async def main():
            from multimer._mpasyncio import create_task, sleep_ms

            ev = MpEvent()

            async def waiter():
                await ev.wait()
                seen.append("done")

            create_task(waiter())
            await sleep_ms(20)
            ev.set()
            await sleep_ms(20)

        mp_run(main())
        self.assertEqual(seen, ["done"])

    def test_clear_requires_new_set(self):
        ev = MpEvent()
        ev.set()
        ev.clear()
        self.assertFalse(ev.is_set())

    def test_background_task_wakes_event(self):
        """lv_utils-style wait/clear loop driven by another _mpasyncio task."""
        ticks = []

        async def main():
            from multimer._mpasyncio import create_task, sleep_ms

            ev = MpEvent()

            async def refresh_loop():
                while len(ticks) < 3:
                    await ev.wait()
                    ev.clear()
                    ticks.append(1)

            async def ticker():
                while len(ticks) < 3:
                    await sleep_ms(25)
                    ev.set()

            create_task(refresh_loop())
            create_task(ticker())
            await sleep_ms(150)

        mp_run(main())
        self.assertGreaterEqual(len(ticks), 3)


@unittest.skipIf(AsyncTimer is None, "async support not available")
class TestAsyncTimerEvent(unittest.TestCase):
    def test_async_timer_wakes_stdlib_event(self):
        """AsyncTimer + asyncio.Event on CPython (stdlib asyncio path)."""
        ticks = []

        async def main():
            ev = asyncio.Event()

            async def refresh_loop():
                while len(ticks) < 3:
                    await ev.wait()
                    ev.clear()
                    ticks.append(1)

            _refresh_task = asyncio.create_task(refresh_loop())  # noqa: RUF006
            t = AsyncTimer(-1)
            t.init(mode=AsyncTimer.PERIODIC, period=20, callback=lambda _tmr: ev.set())
            await asyncio.sleep(0.12)
            t.deinit()

        asyncio.run(main())
        self.assertGreaterEqual(len(ticks), 3)


if __name__ == "__main__":
    unittest.main()
