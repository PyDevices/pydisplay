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
from board_config import runtime
import lvgl as lv

try:
    from multimer import asyncio
except ImportError:
    asyncio = None

asyncio_available = asyncio is not None

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
        if self.asynchronous:
            if not asyncio_available:
                raise RuntimeError("Cannot run asynchronous event loop. asyncio is not available!")
            self.refresh_event = asyncio.Event()
            self.refresh_task = asyncio.create_task(self.async_refresh())

        if runtime is None:
            raise RuntimeError("LVGL requires board_config.runtime")
        self._timer_sub = runtime.on_tick(self.timer_cb, period=self.delay, async_=asynchronous)

    def deinit(self):
        if getattr(self, "_timer_sub", None) is not None:
            self._timer_sub.deinit()
            self._timer_sub = None
        if self.asynchronous:
            self.refresh_task.cancel()
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
