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

import lvgl as lv

try:
    from multimer import Timer, schedule
except ImportError:
    if sys.platform != "darwin":
        raise RuntimeError("Missing multimer implementation!") from None
    Timer = False
    schedule = None

# Try to determine default timer id

default_timer_id = 0
if sys.platform == "pyboard":
    # stm32 only supports SW timer -1
    default_timer_id = -1

if sys.platform == "rp2":
    # rp2 only supports SW timer -1
    default_timer_id = -1

# Try importing asyncio via multimer (stdlib, uasyncio, or _mpasyncio).

try:
    from multimer._async import asyncio as _aio_mod

    asyncio = _aio_mod
    asyncio_available = asyncio is not None
except ImportError:
    asyncio = None
    asyncio_available = False

##############################################################################


class event_loop:
    _current_instance = None

    def __init__(
        self,
        freq=25,
        timer_id=default_timer_id,
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
        self._aio_timer = None

        self.asynchronous = asynchronous
        if self.asynchronous:
            if not asyncio_available:
                raise RuntimeError("Cannot run asynchronous event loop. asyncio is not available!")
            self._init_async_timers()
        else:
            if Timer:
                self.timer = Timer(timer_id)
                self.timer.init(mode=Timer.PERIODIC, period=self.delay, callback=self.timer_cb)
            self.task_handler_ref = self.task_handler  # Allocation occurs here
            self.max_scheduled = max_scheduled
            self.scheduled = 0

    def _init_async_timers(self):
        from multimer import AsyncTimer

        self.refresh_event = asyncio.Event()
        self.refresh_task = asyncio.create_task(self.async_refresh())
        self._aio_timer = AsyncTimer(-1)
        self._aio_timer.init(mode=AsyncTimer.PERIODIC, period=self.delay, callback=self._aio_tick)

    def init_async(self):
        self._init_async_timers()

    def deinit(self):
        if self.asynchronous:
            self.refresh_task.cancel()
            if self._aio_timer is not None:
                self._aio_timer.deinit()
                self._aio_timer = None
        else:
            if Timer:
                self.timer.deinit()
        event_loop._current_instance = None

    def shutdown_for_quit(self, *, pump_rounds=30, pump_delay_ms=1):
        """Stop LVGL scheduling, drain in-flight work, then release the event loop."""
        self.disable()
        if self.asynchronous:
            if self._aio_timer is not None:
                self._aio_timer.deinit()
                self._aio_timer = None
        elif Timer and getattr(self, "timer", None):
            self.timer.deinit()
            self.timer = None

        try:
            from multimer import sleep_ms
        except ImportError:

            def sleep_ms(_ms):
                return None

        for _ in range(pump_rounds):
            sleep_ms(0)
            if lv._nesting.value == 0 and (self.asynchronous or self.scheduled <= 0):
                break
            sleep_ms(pump_delay_ms)

        if lv._nesting.value == 0:
            try:
                lv.task_handler()
            except Exception:
                pass

        if self.asynchronous:
            self.refresh_task.cancel()
        event_loop._current_instance = None

    def disable(self):
        self.scheduled += self.max_scheduled

    def enable(self):
        self.scheduled -= self.max_scheduled

    @staticmethod
    def is_running():
        return event_loop._current_instance is not None

    @staticmethod
    def current_instance():
        return event_loop._current_instance

    def task_handler(self, _):
        if event_loop._current_instance is not self:
            if getattr(self, "scheduled", 0) > 0:
                self.scheduled -= 1
            return
        try:
            nesting = lv._nesting.value
            if nesting == 0:
                lv.task_handler()
                if self.refresh_cb:
                    self.refresh_cb()
            self.scheduled -= 1
        except Exception as e:
            if self.exception_sink:
                self.exception_sink(e)

    def tick(self):
        self.timer_cb(None)

    def run(self):
        if sys.platform == "darwin":
            while True:
                self.tick()

    def timer_cb(self, t):
        if event_loop._current_instance is not self:
            return
        # Can be called in Interrupt context
        # Use task_handler_ref since passing self.task_handler would cause allocation.
        lv.tick_inc(self.delay)
        if self.scheduled < self.max_scheduled:
            try:
                schedule(self.task_handler_ref, 0)
                self.scheduled += 1
            except Exception:
                pass

    def _aio_tick(self, _timer):
        lv.tick_inc(self.delay)
        self.refresh_event.set()

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
