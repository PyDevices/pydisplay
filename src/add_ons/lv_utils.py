##############################################################################
# Event Loop module: advancing tick count and scheduling lvgl task handler.
# Import after lvgl module.
# This should be imported and used by display driver.
# Display driver should first check if an event loop is already running.
#
# Usage example with SDL:
#
#        SDL.init(auto_refresh=False)
#        # Register SDL display driver.
#        # Register SDL mouse driver
#        event_loop = lv_utils.event_loop()
#
#
# asyncio example with SDL:
#
#        SDL.init(auto_refresh=False)
#        # Register SDL display driver.
#        # Register SDL mouse driver
#        event_loop = lv_utils.event_loop(asynchronous=True)
#        asyncio.Loop.run_forever()
#
# asyncio example with ili9341:
#
#        event_loop = lv_utils.event_loop(asynchronous=True) # Optional!
#        self.disp = ili9341(asynchronous=True)
#        asyncio.Loop.run_forever()
#
# MIT license; Copyright (c) 2021 Amir Gonnen
#
##############################################################################

import sys

# pydisplay changes from upstream lv_utils.py (kept intentionally small):
#   * The periodic tick is provided by the board's shared runtime timer
#     (``eventsys.Runtime.on_tick``) instead of a ``machine.Timer``.
#   * ``asyncio`` comes from ``multimer`` (public API).
#   * The sync path runs ``lv.task_handler()`` straight from the tick callback
#     (guarded against re-entrancy) rather than via ``micropython.schedule``;
#     the runtime timer already delivers the callback on the main thread.
#   * Async mode arms the asyncio refresh task lazily on the first timer tick
#     (inside the running loop) so ``import display_driver`` at module-top
#     level is safe before any event loop exists.
#   * No application loop helper: LVGL apps just call ``runtime.run_forever()``.
from board_config import runtime
import lvgl as lv

try:
    from multimer import asyncio
except ImportError:
    asyncio = None

asyncio_available = asyncio is not None


def _asyncio_loop_running():
    """True when an asyncio loop is already running (host loop or inside a task)."""
    if asyncio is None:
        return False
    if hasattr(asyncio, "get_running_loop"):
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    return False


##############################################################################


class event_loop:
    _current_instance = None

    def __init__(
        self,
        freq=25,
        max_scheduled=2,
        refresh_cb=None,
        asynchronous=False,
        exception_sink=None,
    ):
        if self.is_running():
            raise RuntimeError("Event loop is already running!")

        if not lv.is_initialized():
            lv.init()

        event_loop._current_instance = self

        self.delay = 1000 // freq
        self.refresh_cb = refresh_cb
        self.exception_sink = exception_sink if exception_sink else self.default_exception_sink
        self._pause = 0
        self._in_task = False

        self.asynchronous = asynchronous
        self.refresh_task = None
        self._timer_sub = None
        self._async_armed = False

        if runtime is None:
            raise RuntimeError("LVGL requires board_config.runtime")

        if self.asynchronous:
            if not asyncio_available:
                raise RuntimeError("Cannot run asynchronous event loop. asyncio is not available!")
            self.refresh_event = asyncio.Event()
            # The async refresh task and AsyncTimer both need a running asyncio
            # loop. If one is already running (host loop on PyScript/Jupyter, or
            # imported from within a task) arm immediately; otherwise defer until
            # arm() is called once the loop starts (e.g. from lv_utils.run_forever
            # or display_driver's at-exit auto-run). This lets ``import
            # display_driver`` sit at module top level before any loop exists.
            if _asyncio_loop_running():
                self.arm()
        else:
            self._timer_sub = runtime.on_tick(self.timer_cb, period=self.delay, async_=False)

    def arm(self):
        """Create the async refresh task + shared timer once a loop is running.

        No-op in sync mode or when already armed. Safe to call repeatedly.
        """
        if not self.asynchronous or self._async_armed:
            return
        self._async_armed = True
        self.refresh_task = asyncio.create_task(self.async_refresh())
        self._timer_sub = runtime.on_tick(self.timer_cb, period=self.delay, async_=True)

    def deinit(self):
        if getattr(self, "_timer_sub", None) is not None:
            self._timer_sub.deinit()
            self._timer_sub = None
        if self.asynchronous and self.refresh_task is not None:
            self.refresh_task.cancel()
            self.refresh_task = None
        self._async_armed = False
        event_loop._current_instance = None

    def disable(self):
        # Pause LVGL task handling (e.g. while building the UI). Re-entrant.
        self._pause += 1

    def enable(self):
        if self._pause > 0:
            self._pause -= 1

    @staticmethod
    def is_running():
        return event_loop._current_instance is not None

    @staticmethod
    def current_instance():
        return event_loop._current_instance

    def task_handler(self, _=None):
        if self._in_task or self._pause > 0:
            return
        self._in_task = True
        try:
            if lv._nesting.value == 0:
                lv.task_handler()
                if self.refresh_cb:
                    self.refresh_cb()
        except Exception as e:
            if self.exception_sink:
                self.exception_sink(e)
        finally:
            self._in_task = False

    def tick(self):
        self.timer_cb(None)

    def run(self):
        if sys.platform == "darwin":
            while True:
                self.tick()

    def timer_cb(self, t):
        # Called from the runtime's shared timer (on the main thread).
        # In async mode the AsyncTimer fires from inside the running asyncio
        # loop, so we can safely arm (create the refresh task) on the first
        # tick — no need for an external coordinator.
        if self.asynchronous and not self._async_armed:
            self.arm()
        lv.tick_inc(self.delay)
        if self._pause > 0:
            return
        if self.asynchronous:
            self.refresh_event.set()
        else:
            self.task_handler()

    async def async_refresh(self):
        while True:
            await self.refresh_event.wait()
            if lv._nesting.value == 0:
                self.refresh_event.clear()
                try:
                    lv.task_handler()
                except Exception as e:
                    if self.exception_sink:
                        self.exception_sink(e)
                if self.refresh_cb:
                    self.refresh_cb()

    def default_exception_sink(self, e):
        sys.print_exception(e)
        # event_loop.current_instance().deinit()
