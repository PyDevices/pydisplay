# SPDX-FileCopyrightText: 2024 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""
display_driver.py - LVGL driver configuration for pydisplay.  Requires a valid
board_config.py to be in a directory on the micropython path.
"""

import gc
import sys

from board_config import broker, display_drv

try:
    from board_config import TIMER_ASYNC
except ImportError:
    TIMER_ASYNC = False

import lv_utils
import lvgl as lv

import eventsys
from eventsys import events


def main():
    gc.collect()
    if not lv.is_initialized():
        lv.init()
    if not lv_utils.event_loop.is_running():
        # Async apps use multimer.AsyncTimer for LVGL ticks; SDL auto_refresh uses sync
        # multimer.Timer (_threading on CircuitPython) which requires pump().
        # Present the frame from the aio refresh loop instead.
        refresh_cb = None
        if TIMER_ASYNC:
            if getattr(display_drv, "_timer", None) is not None:
                display_drv._timer.deinit()
                display_drv._timer = None
            refresh_cb = display_drv.show
        lv_utils.event_loop(asynchronous=TIMER_ASYNC, refresh_cb=refresh_cb)

    if lv.group_get_default() is None:
        lv.group_create().set_default()

    _dd = DisplayDriver(
        display_drv,
        broker.devices,
    )

    def _lvgl_deinit():
        inst = lv_utils.event_loop.current_instance()
        if inst is not None:
            inst.deinit()

    broker.register_quit_cleanup(display_drv, before=_lvgl_deinit)


class _TouchState:
    x = 0
    y = 0
    pressed = False


def _touch_cb(event, indev, data):
    # LVGL read_cb must report current pointer state on every call, not only when
    # a new event arrives.
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
    # LVGL hands us an object called data.  We just change the enc_diff and/or state attributes if necessary.
    if event is None:
        return
    if event.type == events.MOUSEWHEEL:
        data.enc_diff = event.x if event.flipped is False else -event.x
    elif event.type == events.MOUSEBUTTONDOWN and event.button == 3:
        data.state = lv.INDEV_STATE.PRESSED
    elif event.type == events.MOUSEBUTTONUP and event.button == 3:
        data.state = lv.INDEV_STATE.RELEASED


def _keypad_cb(event, indev, data):
    # LVGL hands us an object called data.  We just change the state attributes when necessary.
    if event is None:
        return
    if event.type == events.KEYDOWN:
        data.state = lv.INDEV_STATE.PRESSED
        data.key = event.key
    elif event.type == events.KEYUP:
        data.state = lv.INDEV_STATE.RELEASED
        data.key = event.key


def create_devices(devs, lv_display):
    # Create an input device for each device in the 'devices' list
    # and set its type and read callback function.  Save a reference to the indev object
    # in the device's user_data attribute to enable changing the indev's group or display
    # later with:
    #     indev = device.user_data
    #     indev.set_group(new_group)
    #     indev.set_display(new_display)
    for device in devs:
        if device.type in (eventsys.TOUCH, eventsys.ENCODER, eventsys.KEYPAD):
            indev = lv.indev_create()
            indev.set_display(lv_display)
            device.user_data = indev
            if device.type == eventsys.TOUCH:
                device.subscribe(_touch_cb)  # Called by device
                indev.set_type(lv.INDEV_TYPE.POINTER)
            elif device.type == eventsys.ENCODER:
                device.subscribe(_encoder_cb)  # Called by device
                indev.set_type(lv.INDEV_TYPE.ENCODER)
            elif device.type == eventsys.KEYPAD:
                device.subscribe(_keypad_cb)  # Called by device
                indev.set_type(lv.INDEV_TYPE.KEYPAD)
            indev.set_group(lv.group_get_default())
            indev.set_read_cb(device.poll)  # Called by lv task handler
        elif device.type == eventsys.QUEUE:
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
        # If byte swapping is required and the display bus is capable of having byte swapping disabled,
        # disable it and set a flag so we can swap the color bytes as they are created.
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
        width = area.x2 - area.x1 + 1
        height = area.y2 - area.y1 + 1

        # Swap the bytes in the color buffer if necessary
        if self._needs_swap:
            lv.draw_sw_rgb565_swap(color_p, width * height)

        # we have to use the __dereference__ method because this method
        # converts from the C_Array object the binding passes into a
        # memoryview object that can be passed to the bus drivers
        data = color_p.__dereference__(width * height * self._color_size)
        display_drv.blit_rect(data, area.x1, area.y1, width, height)
        if self._blocking:
            self.lv_display.flush_ready()


def run():
    """
    Keep LVGL alive on the main thread when a blocking loop is required.

    On MicroPython unix and CPython (non-Windows), ``lv_utils`` already started
    a periodic timer at ``import display_driver`` time — this returns immediately
    so the REPL stays usable while the UI runs.

    On Windows (MicroPython and CPython), blocks in ``pump()`` +
    ``broker.poll()`` because the SDL message pump needs the main thread.

    On macOS, blocks in ``lv_utils.event_loop.run()`` (manual tick loop).
    """
    from multimer import needs_pump, pump, sleep_ms

    inst = lv_utils.event_loop.current_instance()
    if inst is not None:
        if sys.platform == "darwin":
            inst.run()
            return
        if sys.platform != "win32":
            return

    while True:
        if needs_pump():
            pump()
        if elist := broker.poll():
            for e in elist:
                if e.type == events.QUIT:
                    return
        sleep_ms(1)


main()
