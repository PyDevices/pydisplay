# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

import threading
import time
import unittest

import _env  # noqa: F401

import multimer
from multimer import (
    AsyncTimer,
    Timer,
    monotonic,
    sleep_ms,
    ticks_add,
    ticks_diff,
    ticks_less,
    ticks_ms,
)

_TICKS_PERIOD = 1 << 29
_TICKS_MAX = _TICKS_PERIOD - 1

_PUBLIC_TIMER_MEMBERS = {"init", "deinit", "ONE_SHOT", "PERIODIC"}


def _public_class_members(cls):
    return {n for n in dir(cls) if not n.startswith("_")}


class TestApiSurface(unittest.TestCase):
    def test_timer_public_members(self):
        self.assertEqual(_public_class_members(Timer), _PUBLIC_TIMER_MEMBERS)

    def test_async_timer_public_members(self):
        self.assertEqual(_public_class_members(AsyncTimer), _PUBLIC_TIMER_MEMBERS)

    def test_constants_match_micropython(self):
        self.assertEqual(Timer.ONE_SHOT, 0)
        self.assertEqual(Timer.PERIODIC, 1)
        self.assertEqual(AsyncTimer.ONE_SHOT, 0)
        self.assertEqual(AsyncTimer.PERIODIC, 1)

    def test_package_exports(self):
        self.assertEqual(
            set(multimer.__all__),
            {
                "Timer",
                "AsyncTimer",
                "monotonic",
                "run_deadline_hook",
                "schedule",
                "set_deadline_hook",
                "uses_signals",
                "sleep_ms",
                "ticks_ms",
                "ticks_add",
                "ticks_diff",
                "ticks_less",
                "asyncio",
                "install_asyncio_compat",
            },
        )


class TestTicks(unittest.TestCase):
    def test_ticks_ms_in_range(self):
        t = ticks_ms()
        self.assertIsInstance(t, int)
        self.assertGreaterEqual(t, 0)
        self.assertLessEqual(t, _TICKS_MAX)

    def test_monotonic_advances(self):
        start = monotonic()
        self.assertIsInstance(start, (int, float))
        sleep_ms(20)
        self.assertGreaterEqual(monotonic(), start)

    def test_ticks_add_wrap(self):
        self.assertEqual(ticks_add(_TICKS_MAX, 1), 0)

    def test_ticks_diff_wrap(self):
        later = ticks_add(_TICKS_MAX, 10)
        self.assertEqual(ticks_diff(later, _TICKS_MAX), 10)

    def test_ticks_less(self):
        self.assertTrue(ticks_less(100, 200))

    def test_sleep_ms_advances_time(self):
        start = ticks_ms()
        sleep_ms(50)
        self.assertGreaterEqual(ticks_diff(ticks_ms(), start), 40)


class TestTimerSemantics(unittest.TestCase):
    def test_periodic_fires(self):
        hits = []
        main_thread = threading.get_ident()
        callback_threads = []

        def cb(t):
            hits.append(t)
            callback_threads.append(threading.get_ident())

        t = Timer(-1)
        t.init(period=50, callback=cb)
        deadline = time.monotonic() + 0.35
        while time.monotonic() < deadline:
            time.sleep(0.01)
        t.deinit()
        self.assertGreaterEqual(len(hits), 2)
        self.assertIs(hits[0], t)
        self.assertTrue(callback_threads)
        self.assertEqual(set(callback_threads), {main_thread})

    def test_one_shot_fires_once(self):
        hits = []
        main_thread = threading.get_ident()
        callback_threads = []

        def cb(t):
            hits.append(t)
            callback_threads.append(threading.get_ident())

        t = Timer(-1)
        t.init(mode=Timer.ONE_SHOT, period=50, callback=cb)
        time.sleep(0.2)
        self.assertEqual(len(hits), 1)
        self.assertEqual(callback_threads, [main_thread])

    def test_freq_overrides_period(self):
        hits = []

        t = Timer(-1)
        t.init(freq=20, period=1, callback=lambda _t: hits.append(1))
        time.sleep(0.25)
        t.deinit()
        self.assertGreaterEqual(len(hits), 2)
        self.assertLessEqual(len(hits), 12)


class TestAsyncTimer(unittest.TestCase):
    def test_requires_running_loop(self):
        t = AsyncTimer(-1)
        with self.assertRaises(RuntimeError):
            t.init(period=20, callback=lambda _t: None)

    def test_periodic_under_asyncio(self):
        import asyncio as std_asyncio

        hits = []
        main_thread = threading.get_ident()
        callback_threads = []

        async def main():
            t = AsyncTimer(-1)
            t.init(
                period=20,
                callback=lambda tim: (
                    hits.append(tim),
                    callback_threads.append(threading.get_ident()),
                ),
            )
            await std_asyncio.sleep(0.15)
            t.deinit()

        std_asyncio.run(main())
        self.assertGreaterEqual(len(hits), 2)
        self.assertEqual(set(callback_threads), {main_thread})


class TestAsyncioCompat(unittest.TestCase):
    def test_backend_contract_is_unchanged(self):
        from multimer import asyncio, asyncio_compat

        self.assertIs(asyncio_compat.backend(), asyncio)

    def test_run_delegates_without_running_loop(self):
        from multimer import asyncio_compat

        async def main():
            return 42

        self.assertEqual(asyncio_compat.run(main()), 42)

    def test_run_schedules_inside_running_loop(self):
        from multimer import asyncio, asyncio_compat

        async def child():
            await asyncio.sleep(0)
            return 42

        async def main():
            loop = asyncio.get_running_loop()
            task = asyncio_compat.run(child())
            self.assertIs(asyncio_compat.new_event_loop(), loop)
            self.assertEqual(await task, 42)

        asyncio.run(main())

    def test_zero_delay_sleeps_yield_to_browser_host(self):
        from multimer import asyncio, asyncio_compat

        calls = []

        class Backend:
            @staticmethod
            async def sleep(delay):
                calls.append(("sleep", delay))

            @staticmethod
            async def sleep_ms(delay):
                calls.append(("sleep_ms", delay))

        old_backend = asyncio_compat._backend

        async def main():
            asyncio_compat._backend = Backend()
            try:
                await asyncio_compat.sleep(0)
                await asyncio_compat.sleep_ms(0)
                await asyncio_compat.sleep(2)
                await asyncio_compat.sleep_ms(3)
            finally:
                asyncio_compat._backend = old_backend

        asyncio.run(main())
        self.assertEqual(
            calls,
            [("sleep", 0.001), ("sleep_ms", 1), ("sleep", 2), ("sleep_ms", 3)],
        )

    def test_installer_replaces_module_names_only(self):
        import sys

        from multimer import asyncio

        old_asyncio = sys.modules.get("asyncio")
        old_uasyncio = sys.modules.get("uasyncio")
        try:
            facade = multimer.install_asyncio_compat()
            self.assertIs(sys.modules["asyncio"], facade)
            self.assertIs(sys.modules["uasyncio"], facade)
            self.assertIs(multimer.asyncio, asyncio)
            self.assertIs(multimer.install_asyncio_compat(), facade)
        finally:
            if old_asyncio is None:
                sys.modules.pop("asyncio", None)
            else:
                sys.modules["asyncio"] = old_asyncio
            if old_uasyncio is None:
                sys.modules.pop("uasyncio", None)
            else:
                sys.modules["uasyncio"] = old_uasyncio


class TestSchedule(unittest.TestCase):
    def test_schedule_main_thread(self):
        seen = []
        multimer.schedule(seen.append, 42)
        self.assertEqual(seen, [42])


if __name__ == "__main__":
    unittest.main()
