# SPDX-FileCopyrightText: 2024 Brad Barnett
# SPDX-FileCopyrightText: 2021 Amir Gonnen (event_loop; MIT)
#
# SPDX-License-Identifier: MIT

"""
display_driver.py - LVGL display/input wiring and event loop for pydisplay.

Requires a valid board_config.py on the path. Importing this module initializes
LVGL, starts the shared ``event_loop`` (tick via ``runtime.on_tick``), and
registers display flush + input devices.

``event_loop`` was adapted from upstream lv_utils (Amir Gonnen). pydisplay
changes kept intentionally small:

* Periodic tick from ``eventsys.Runtime.on_tick`` instead of ``machine.Timer``.
* ``asyncio`` from ``multimer``.
* Sync path runs ``lv.task_handler()`` from the tick callback (re-entrancy
  guarded); the runtime timer already delivers on the main thread.
* Async mode arms the refresh task lazily on the first timer tick so module-top
  ``import display_driver`` is safe before any event loop exists.
* No app-loop helper — LVGL apps call ``runtime.run_forever()``.
"""

import gc
import sys

from board_config import display_drv, runtime
import lvgl as lv

import eventsys
from eventsys import events

try:
    from multimer import asyncio
except ImportError:
    asyncio = None

asyncio_available = asyncio is not None

_driver_ref = None


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
            # arm() is called once the loop starts. This lets ``import
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


def main():
    global _driver_ref
    gc.collect()
    if not lv.is_initialized():
        lv.init()
    if not event_loop.is_running():
        if runtime is not None:
            runtime.claim_display_refresh()
        loop_inst = event_loop(
            asynchronous=runtime.timer_async if runtime is not None else False,
            refresh_cb=display_drv.show,
        )
    else:
        loop_inst = event_loop.current_instance()

    if loop_inst is not None:
        loop_inst.disable()
    try:
        if lv.group_get_default() is None:
            lv.group_create().set_default()

        devs = runtime.devices if runtime is not None else []
        _driver_ref = DisplayDriver(
            display_drv,
            devs,
        )
    finally:
        if loop_inst is not None:
            loop_inst.enable()

    if runtime is not None:

        def _lvgl_shutdown_before_quit():
            # Runs from Runtime._handle_quit (device QUIT or at-exit) before the
            # shared timer stops and the display is released. Tear LVGL down in
            # order: stop the event loop, then lv.deinit() to release LVGL's C
            # state so nothing dereferences it during interpreter finalization.
            inst = event_loop.current_instance()
            if inst is not None:
                inst.deinit()
            try:
                if lv.is_initialized():
                    lv.deinit()
            except Exception:
                pass

        runtime.before_quit = _lvgl_shutdown_before_quit


class _TouchState:
    x = 0
    y = 0
    pressed = False


def _touch_cb(event, indev, data):
    if event is not None:
        if event.type == events.MOUSEBUTTONDOWN and event.button == 1:
            _TouchState.x, _TouchState.y = event.pos
            _TouchState.pressed = True
        elif event.type == events.MOUSEMOTION and event.buttons[0]:
            _TouchState.x, _TouchState.y = event.pos
        elif event.type == events.MOUSEBUTTONUP and event.button == 1:
            _TouchState.x, _TouchState.y = event.pos
            _TouchState.pressed = False
    data.point = lv.point_t({"x": _TouchState.x, "y": _TouchState.y})
    data.state = lv.INDEV_STATE.PRESSED if _TouchState.pressed else lv.INDEV_STATE.RELEASED


def _encoder_cb(event, indev, data):
    if event is None:
        return
    if event.type == events.MOUSEWHEEL:
        data.enc_diff = event.x if event.flipped is False else -event.x
    elif event.type == events.MOUSEBUTTONDOWN and event.button == 3:
        data.state = lv.INDEV_STATE.PRESSED
    elif event.type == events.MOUSEBUTTONUP and event.button == 3:
        data.state = lv.INDEV_STATE.RELEASED


def _keypad_cb(event, indev, data):
    if event is None:
        return
    if event.type == events.KEYDOWN:
        data.state = lv.INDEV_STATE.PRESSED
        data.key = event.key
    elif event.type == events.KEYUP:
        data.state = lv.INDEV_STATE.RELEASED
        data.key = event.key


def create_devices(devs, lv_display):
    for device in devs:
        if device.type in (eventsys.POINTER, eventsys.ENCODER, eventsys.KEYPAD):
            indev = lv.indev_create()
            indev.set_display(lv_display)
            device.user_data = indev
            if device.type == eventsys.POINTER:
                device.subscribe(_touch_cb)
                indev.set_type(lv.INDEV_TYPE.POINTER)
            elif device.type == eventsys.ENCODER:
                device.subscribe(_encoder_cb)
                indev.set_type(lv.INDEV_TYPE.ENCODER)
            elif device.type == eventsys.KEYPAD:
                device.subscribe(_keypad_cb)
                indev.set_type(lv.INDEV_TYPE.KEYPAD)
            indev.set_group(lv.group_get_default())
            indev.set_read_cb(device.poll)
        elif device.type == eventsys.HOST:
            vd = eventsys.VirtualDevices(device)
            create_devices(vd.devices, lv_display)


class DisplayDriver:
    def __init__(
        self,
        display_drv,
        devs=None,
        color_format=lv.COLOR_FORMAT.RGB565,
        blocking=True,
    ):
        if devs is None:
            devs = []
        gc.collect()
        if display_drv.requires_byteswap:
            self._needs_swap = display_drv.disable_auto_byteswap(True)
        else:
            self._needs_swap = False
        self._color_size = lv.color_format_get_size(color_format)
        self._blocking = blocking

        self._draw_buf1 = lv.draw_buf_create(
            display_drv.width, display_drv.height // 10, color_format, 0
        )
        self._draw_buf2 = lv.draw_buf_create(
            display_drv.width, display_drv.height // 10, color_format, 0
        )

        self.lv_display = lv.display_create(display_drv.width, display_drv.height)
        self.lv_display.set_flush_cb(self._flush_cb)
        self.lv_display.set_color_format(color_format)
        if not self._blocking:
            display_drv.display_bus.register_callback(self.lv_display.flush_ready)
        self.lv_display.set_draw_buffers(self._draw_buf1, self._draw_buf2)
        self.lv_display.set_render_mode(lv.DISPLAY_RENDER_MODE.PARTIAL)
        create_devices(devs, self.lv_display)

    def _flush_cb(self, disp_drv, area, color_p):
        if hasattr(display_drv, "_sdl_active") and not display_drv._sdl_active():
            self.lv_display.flush_ready()
            return
        width = area.x2 - area.x1 + 1
        height = area.y2 - area.y1 + 1

        if self._needs_swap:
            lv.draw_sw_rgb565_swap(color_p, width * height)

        data = color_p.__dereference__(width * height * self._color_size)
        display_drv.blit_rect(data, area.x1, area.y1, width, height)
        if self._blocking:
            self.lv_display.flush_ready()


main()
