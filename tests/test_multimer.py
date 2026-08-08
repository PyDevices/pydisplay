# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

import sys
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
                "backend_name",
                "backends",
                "backends_available",
                "loop_running",
                "monotonic",
                "run_deadline_hook",
                "schedule",
                "set_deadline_hook",
                "use_backend",
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


class TestBackendSelection(unittest.TestCase):
    """``backend_name`` / ``use_backend`` — the supported way to pick a backend."""

    def setUp(self):
        self._original = multimer.backend_name()

    def tearDown(self):
        multimer.use_backend(self._original)

    def test_backend_name_is_a_known_backend(self):
        self.assertIn(multimer.backend_name(), multimer.backends())

    def test_backends_has_no_win32(self):
        self.assertNotIn("win32", multimer.backends())

    def test_backends_order_matches_auto_then_async(self):
        self.assertEqual(
            multimer.backends(),
            ("machine", "librt", "sdl2", "threading", "polling", "async"),
        )

    def test_auto_backends_skips_sdl2_when_pygame_present(self):
        from multimer import _select

        self.assertEqual(sys.implementation.name, "cpython")
        self.assertTrue(_select._pygame_available())
        self.assertNotIn("sdl2", _select._auto_backends())
        # Explicit override list still includes sdl2.
        self.assertIn("sdl2", multimer.backends())
        self.assertNotEqual(multimer.backend_name(), "sdl2")

    def test_auto_backends_allows_sdl2_on_cpython_without_pygame(self):
        from unittest import mock

        from multimer import _select

        with mock.patch.object(_select, "_pygame_available", return_value=False):
            self.assertIn("sdl2", _select._auto_backends())

    def test_backends_available_is_subset(self):
        available = multimer.backends_available()
        self.assertTrue(available)
        self.assertTrue(set(available).issubset(set(multimer.backends())))
        self.assertIn(multimer.backend_name(), available)

    def test_backends_available_does_not_change_active(self):
        before = multimer.backend_name()
        multimer.backends_available()
        self.assertEqual(multimer.backend_name(), before)

    def test_use_backend_rebinds_timer_and_sleep(self):
        multimer.use_backend("polling")
        self.assertEqual(multimer.backend_name(), "polling")
        self.assertEqual(multimer.Timer.__module__, "multimer._backends.polling")
        # ``from multimer import Timer`` must see the same class as multimer.Timer.
        from multimer import _timer

        self.assertIs(_timer.Timer, multimer.Timer)
        self.assertFalse(multimer.uses_signals())

    def test_use_backend_returns_active_name(self):
        self.assertEqual(multimer.use_backend("polling"), "polling")

    def test_async_backend_selects_awaitable_sleep(self):
        multimer.use_backend("async")
        self.assertIs(multimer.Timer, AsyncTimer)
        # ``sleep_ms`` must be awaitable here, not a blocking sleep.
        coro = multimer.sleep_ms(0)
        self.addCleanup(coro.close)
        self.assertTrue(hasattr(coro, "send"))

    def test_unknown_backend_raises_value_error(self):
        with self.assertRaises(ValueError):
            multimer.use_backend("no_such_backend")

    def test_unavailable_backend_raises_import_error(self):
        # ``machine.Timer`` is absent on CPython desktop; the selection must not
        # fall back silently when a caller asks for a specific backend.
        try:
            from machine import Timer as _MachineTimer  # noqa: F401
        except ImportError:
            pass
        else:
            self.skipTest("machine.Timer is available on this host")
        with self.assertRaises(ImportError):
            multimer.use_backend("machine")

    def test_restores_previous_backend(self):
        before = multimer.backend_name()
        multimer.use_backend("polling")
        multimer.use_backend(before)
        self.assertEqual(multimer.backend_name(), before)

    def test_context_manager_deinits(self):
        hits = []
        with Timer(-1) as t:
            t.init(period=20, callback=lambda _t: hits.append(1))
            for _ in range(8):
                sleep_ms(10)
        self.assertGreaterEqual(len(hits), 1)
        # After exit the timer must be disarmed.
        n = len(hits)
        sleep_ms(50)
        self.assertEqual(len(hits), n)


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
        for _ in range(35):
            sleep_ms(10)
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
        for _ in range(25):
            sleep_ms(10)
        self.assertEqual(len(hits), 1)
        self.assertEqual(callback_threads, [main_thread])

    def test_freq_overrides_period(self):
        hits = []

        t = Timer(-1)
        t.init(freq=20, period=1, callback=lambda _t: hits.append(1))
        for _ in range(25):
            sleep_ms(10)
        t.deinit()
        self.assertGreaterEqual(len(hits), 2)
        self.assertLessEqual(len(hits), 12)

    def test_soft_coalesce_under_threading(self):
        """``hard=False`` must go through ``_deliver`` (coalesce), not raw invoke."""
        original = multimer.backend_name()
        try:
            try:
                multimer.use_backend("threading")
            except ImportError:
                self.skipTest("threading backend unavailable")
            hits = []

            def cb(_t):
                hits.append(1)
                multimer.sleep_ms(40)

            t = multimer.Timer(-1)
            t.init(period=10, callback=cb, hard=False)
            # Use ``multimer.sleep_ms`` (rebound by use_backend), not the
            # module-level import captured under the previous backend.
            for _ in range(20):
                multimer.sleep_ms(10)
            t.deinit()
            # Without coalesce a 10 ms period over ~200 ms would enqueue many more.
            self.assertGreaterEqual(len(hits), 1)
            self.assertLessEqual(len(hits), 8)
        finally:
            multimer.use_backend(original)


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


class TestLoopRunning(unittest.TestCase):
    def test_false_outside_a_loop(self):
        self.assertFalse(multimer.loop_running())

    def test_true_inside_a_loop(self):
        from multimer import asyncio

        async def main():
            return multimer.loop_running()

        self.assertTrue(asyncio.run(main()))

    def test_ignores_get_event_loop(self):
        """``get_event_loop`` returns a loop even when none runs, so it must not be used.

        A backend offering only ``get_event_loop`` has to report "no loop" rather
        than trusting it — the case that made eventsys defer async timers forever
        on MicroPython.
        """
        from multimer import _asyncio_loader

        class OnlyGetEventLoop:
            def get_event_loop(self):
                return "a loop that is not running"

        saved = _asyncio_loader._asyncio_mod
        _asyncio_loader._asyncio_mod = OnlyGetEventLoop()
        try:
            self.assertFalse(_asyncio_loader.loop_running())
        finally:
            _asyncio_loader._asyncio_mod = saved

    def test_prefers_current_task_over_get_running_loop(self):
        """CircuitPython's ``get_running_loop()`` succeeds with no loop running."""
        from multimer import _asyncio_loader

        class LyingGetRunningLoop:
            def current_task(self):
                return None

            def get_running_loop(self):
                return "a loop that is not running"

        saved = _asyncio_loader._asyncio_mod
        _asyncio_loader._asyncio_mod = LyingGetRunningLoop()
        try:
            self.assertFalse(_asyncio_loader.loop_running())
        finally:
            _asyncio_loader._asyncio_mod = saved


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

    def test_installer_survives_uasyncio_name_shim(self):
        """MicroPython ``uasyncio`` forwards into ``sys.modules['asyncio']``.

        If the loader cached that shim and the facade then replaced ``asyncio``,
        ``loop_running`` / ``getattr(current_task)`` used to recurse forever.
        """
        import types

        from multimer import _asyncio_loader, asyncio_compat

        real = sys.modules["asyncio"]
        old_cached = _asyncio_loader._asyncio_mod
        old_backend = asyncio_compat._backend
        old_uasyncio = sys.modules.get("uasyncio")

        shim = types.ModuleType("uasyncio")

        def _shim_getattr(name):
            return getattr(sys.modules["asyncio"], name)

        shim.__getattr__ = _shim_getattr  # type: ignore[attr-defined]
        shim.create_task = real.create_task  # load_asyncio probe

        try:
            sys.modules["uasyncio"] = shim
            _asyncio_loader._asyncio_mod = shim
            asyncio_compat._backend = shim

            facade = multimer.install_asyncio_compat()
            self.assertIs(sys.modules["asyncio"], facade)
            self.assertIs(asyncio_compat._backend, real)
            self.assertIs(_asyncio_loader._asyncio_mod, real)
            # Must not recurse through shim → facade → shim.
            self.assertTrue(callable(getattr(sys.modules["uasyncio"], "current_task", None)))
            self.assertFalse(multimer.loop_running())
        finally:
            _asyncio_loader._asyncio_mod = old_cached
            asyncio_compat._backend = old_backend
            sys.modules["asyncio"] = real
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
