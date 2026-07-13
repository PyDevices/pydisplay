# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Tests for runtime-owned display auto-refresh."""

import time
import unittest

import _env  # noqa: F401

from eventsys import Runtime
from multimer import sleep_ms


class _FakeDisplay:
    needs_refresh = True

    def __init__(self):
        self.shows = 0
        self.last_arg = "unset"
        self.quitted = False

    def show(self, timer=None):
        self.shows += 1
        self.last_arg = timer

    def quit(self):
        self.quitted = True


def _wait(predicate, timeout_s=1.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        sleep_ms(5)
    return predicate()


class TestRuntimeOwnedRefresh(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime()

    def tearDown(self):
        self.runtime.stop_timer()

    def test_on_tick_starts_shared_timer(self):
        self.assertIsNone(self.runtime._timer)
        hits = []
        self.runtime.on_tick(hits.append, period=20)
        self.assertIsNotNone(self.runtime._timer)
        self.assertTrue(_wait(lambda: len(hits) > 0), "shared timer never fired")

    def test_constructor_wires_refresh(self):
        display = _FakeDisplay()
        runtime = Runtime(display=display)
        self.addCleanup(runtime.stop_timer)
        self.assertTrue(_wait(lambda: display.shows > 0), "display.show never called")

    def test_test_mode_skips_auto_refresh(self):
        import os
        import sys

        tools = os.path.join(os.path.dirname(__file__), "..", "tools")
        if tools not in sys.path:
            sys.path.insert(0, tools)
        import pydisplay_test_mode

        display = _FakeDisplay()
        try:
            pydisplay_test_mode.ENABLED = True
            runtime = Runtime(display=display)
            self.addCleanup(runtime.stop_timer)
            # Test mode arms the auto-service (so the canonical no-loop idiom's
            # input/QUIT works under the harness) but must not wire the periodic
            # display.show() refresh — examples that show() themselves would
            # otherwise get a competing refresh.
            self.assertIsNotNone(runtime._service_subscription)
            self.assertIsNone(runtime._refresh_subscription)
            sleep_ms(80)
            self.assertEqual(display.shows, 0)
        finally:
            pydisplay_test_mode.ENABLED = False

    def test_timer_async_defers_refresh_until_armed(self):
        display = _FakeDisplay()
        runtime = Runtime(display=display, timer_async=True)
        self.addCleanup(runtime.stop_timer)
        self.assertIsNone(runtime._timer)
        self.assertIsNotNone(runtime._pending_async_refresh)

        async def _arm_and_wait():
            runtime.arm_async_refresh()
            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                if display.shows > 0:
                    return
                await __import__("asyncio").sleep(0.01)
            raise AssertionError("display.show never called")

        import asyncio

        asyncio.run(_arm_and_wait())
        from multimer import AsyncTimer

        self.assertIsInstance(runtime._timer, AsyncTimer)

    def test_sync_refresh_deferred_when_backend_needs_drain(self):
        import multimer._select as sel

        display = _FakeDisplay()
        runtime = Runtime(display=display, timer_async=False)
        self.addCleanup(runtime.stop_timer)
        if not sel._drain:
            self.skipTest("no drain backend on this platform")
        self.assertIsNone(runtime._timer)
        self.assertIsNotNone(runtime._pending_sync_refresh)
        runtime._maybe_arm_pending_sync_refresh()
        self.assertTrue(_wait(lambda: display.shows > 0), "display.show never called")

    def test_subscription_deinit_unsubscribes(self):
        hits = []
        sub = self.runtime.on_tick(hits.append, period=20)
        self.assertTrue(_wait(lambda: len(hits) > 0))
        sub.deinit()
        count = len(hits)
        sleep_ms(80)
        self.assertEqual(len(hits), count)

    def test_stop_timer_clears_everything(self):
        self.runtime.on_tick(lambda t: None, period=20)
        self.assertIsNotNone(self.runtime._timer)
        self.runtime.stop_timer()
        self.assertIsNone(self.runtime._timer)
        self.assertEqual(self.runtime._tick_callbacks, [])


if __name__ == "__main__":
    unittest.main()
